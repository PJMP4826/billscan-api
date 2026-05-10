import base64
from typing import Sequence, cast

from llama_index.core.base.llms.types import ImageBlock
from llama_index.core.llms.llm import LLM
from llama_index.core.program import MultiModalLLMCompletionProgram

from src.domain.entities.receipt import Receipt
from src.domain.ports.receipt_extractor import ReceiptExtractorPort
from src.infrastructure.adapters.http_adapter import HttpClientAdapter
from src.infrastructure.mappers.receipt_mapper import ReceiptMapper
from src.infrastructure.schemas.receipt_data import ReceiptData


class LlamaIndexAiExtractor(ReceiptExtractorPort):
    def __init__(self, http_adapter: HttpClientAdapter, llm_provider: LLM) -> None:
        self._http_adapter = http_adapter
        self._llm_provider = llm_provider

    async def extract_from_url(
        self, images_url: list[str], prompt_template_str: str
    ) -> list[Receipt]:
        receipts: list[Receipt] = []

        for url in images_url:
            image = await self._http_adapter.get_image(url=url)

            image_documents: Sequence[ImageBlock] = [
                ImageBlock(image=base64.b64encode(image.image_bytes))
            ]

            program = MultiModalLLMCompletionProgram.from_defaults(  # type: ignore
                output_cls=ReceiptData,
                image_documents=image_documents,  # type: ignore
                prompt_template_str=prompt_template_str,
                multi_modal_llm=self._llm_provider,
            )

            result_pydantic = cast(ReceiptData, await program.acall())
            receipt = ReceiptMapper.schema_to_domain(
                schema=result_pydantic,
                receipt_id=result_pydantic.transaction.receipt_id or "",
            )
            receipts.append(receipt)

        return receipts
