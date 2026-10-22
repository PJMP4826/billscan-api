from dataclasses import dataclass

from src.application.dtos.billing_customer_dto import BillingCustomerInfoDto
from src.application.dtos.billing_customer_regime_dto import BillingCustomerRegimeDto
from src.domain.enums.tax_regime import TaxRegime


@dataclass(frozen=True)
class CsfFiscalIdentityDto:
    """Datos fiscales leídos de una Constancia de Situación Fiscal (CSF).

    Este DTO describe la constancia **tal cual la reporta el SAT**: puede traer
    varios regímenes simultáneos y vigentes a la vez, por lo que aquí no se
    elige ninguno. La elección del régimen que se enviará al proveedor de
    facturación es una decisión de negocio (del usuario) y se aplica después
    con :meth:`to_billing_customer`.

    Se mantiene separado de
    :class:`~src.application.dtos.billing_customer_dto.BillingCustomerInfoDto`
    para que "lo que leí de la constancia" y "lo que voy a timbrar" no se
    confundan: el segundo exige un régimen único y explícito.
    """

    razon_social: str
    rfc: str
    cp: str
    regimens: list[BillingCustomerRegimeDto]
    address: str | None = None

    @property
    def primary_regimen(self) -> TaxRegime | None:
        """Régimen ya resuelto cuando la constancia reporta exactamente uno."""
        return self.regimens[0].code if len(self.regimens) == 1 else None

    @property
    def needs_regimen_selection(self) -> bool:
        """``True`` si el usuario debe elegir entre varios regímenes vigentes."""
        return len(self.regimens) > 1

    def to_billing_customer(
        self, email: str, regimen: TaxRegime | None = None
    ) -> BillingCustomerInfoDto:
        """Hidrata el DTO que consume el proveedor de facturación.

        El régimen se pide explícitamente para que no se pueda enviar uno
        adivinado: si la constancia trae varios, hay que decidir antes.

        Args:
            regimen: Régimen elegido. Si se omite, solo es válido cuando la
                constancia reporta un único régimen.

        Raises:
            ValueError: si no se indica régimen y la constancia tiene varios
                (o ninguno) que permitan resolverlo sin ambigüedad.
        """
        resolved = regimen or self.primary_regimen
        if resolved is None:
            raise ValueError(
                "La constancia reporta varios regímenes fiscales: "
                "se requiere elegir uno explícitamente."
            )

        return BillingCustomerInfoDto(
            razon_social=self.razon_social,
            rfc=self.rfc,
            email=email,
            regimen=resolved,
            cp=self.cp,
            address=self.address,
        )
