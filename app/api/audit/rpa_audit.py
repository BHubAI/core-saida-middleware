from api.base.endpoints import BaseEndpoint
from api.deps import DBSession, DDLogger
from service.audit.rpa_audit import get_rpa_audit_data


ROUTE_PREFIX = "/api/audit"


class RPAAuditoriaEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["RPA Auditoria"], prefix=ROUTE_PREFIX)

        @self.router.get("/rpa-data")
        def get_rpa_audit(db_session: DBSession, logger: DDLogger):
            try:
                logger.info("Getting RPA audit")

                return get_rpa_audit_data(db_session)
            except Exception as e:
                logger.error(f"Error getting RPA audit: {e}")
                raise e
