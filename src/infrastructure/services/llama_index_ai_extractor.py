import base64
import uuid

from typing import Sequence, cast
from src.config.logger import logger
from llama_index.core.base.llms.types import ImageBlock
from llama_index.core.llms.llm import LLM
from llama_index.core.program import MultiModalLLMCompletionProgram
from src.domain.entities.receipt import Receipt
from src.domain.ports.receipt_extractor import ReceiptExtractorPort
from src.infrastructure.adapters.http_adapter import HttpClientAdapter
from src.infrastructure.mappers.receipt_mapper import ReceiptMapper
from src.infrastructure.schemas.receipt_data import ReceiptData

MAX_RETRIES: int = 3


class LlamaIndexAiExtractor(ReceiptExtractorPort):
    def __init__(self, http_adapter: HttpClientAdapter, llm_provider: LLM) -> None:
        self._http_adapter = http_adapter
        self._llm_provider = llm_provider

    async def extract(
        self, image_pages: list[bytes], prompt_template_str: str
    ) -> Receipt:

        # Un grupo = un ticket. Si el ticket tiene 2+ fotos (páginas),
        # las mandamos TODAS juntas en el mismo image_documents para que
        # el LLM las vea como un solo documento, no como tickets distintos.
        image_documents: Sequence[ImageBlock] = [
            ImageBlock(image=base64.b64encode(page)) for page in image_pages
        ]

        logger.debug(
            f"Comenzando extraccion del ticket ({len(image_documents)} imagen(es))"
        )
        receipt = await self._extract_with_retry(
            image_documents=image_documents,
            prompt_template_str=prompt_template_str,
        )

        logger.debug("Extraccion completada, siguiente...")
        return receipt

    async def _extract_with_retry(
        self,
        image_documents: Sequence[ImageBlock],
        prompt_template_str: str,
    ) -> Receipt:
        """Intenta la extracción hasta MAX_RETRIES veces, alimentando el error
        de validación de dominio al prompt para que el LLM se corrija solo."""
        last_error: str | None = None

        for attempt in range(1, MAX_RETRIES + 1):
            prompt = self._build_prompt(
                base_template=prompt_template_str,
                previous_error=last_error,
                attempt=attempt,
            )

            program = MultiModalLLMCompletionProgram.from_defaults(  # type: ignore
                output_cls=ReceiptData,
                image_documents=image_documents,  # type: ignore
                prompt_template_str=prompt,
                multi_modal_llm=self._llm_provider,
            )

            result_pydantic = cast(ReceiptData, await program.acall())

            try:
                receipt = ReceiptMapper.schema_to_domain(
                    schema=result_pydantic, receipt_uuid=uuid.uuid4().hex
                )
                if attempt > 1:
                    logger.info(
                        "Extracción exitosa en intento %d para receipt %s",
                        attempt,
                        receipt.receipt_uuid,
                    )
                return receipt

            except ValueError as exc:
                last_error = str(exc)
                logger.warning(
                    "Intento %d/%d falló: %s", attempt, MAX_RETRIES, last_error
                )

        raise ValueError(
            f"Extracción fallida tras {MAX_RETRIES} intentos"
            f"Último error: {last_error}"
        )

    @staticmethod
    def _build_prompt(
        base_template: str,
        previous_error: str | None,
        attempt: int,
    ) -> str:
        """Construye el prompt, añadiendo el error del intento anterior si existe."""
        if previous_error is None:
            return base_template

        return (
            f"{base_template}\n\n"
            f"⚠️ ATENCIÓN: El intento #{attempt - 1} falló por "
            f"el siguiente error de validación:\n"
            f"{previous_error}\n\n"
            f"Por favor REVISA la imagen nuevamente y CORRIGE "
            f"específicamente los valores que causaron este error. "
            f"Asegúrate de extraer correctamente: "
            f"subtotal, total, impuestos, descuentos, cantidades y precios unitarios "
            f"para que sean consistentes entre sí."
        )
