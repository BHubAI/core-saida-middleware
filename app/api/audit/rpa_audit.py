from app.api.base.endpoints import BaseEndpoint
from app.api.deps import DBSession, DDLogger
from app.service.audit import rpa_audit


ROUTE_PREFIX = "/api/audit"


class RPAAuditoriaEndpoint(BaseEndpoint):
    def __init__(self):
        super().__init__(tags=["RPA Auditoria"], prefix=ROUTE_PREFIX)

        @self.router.get("/rpa-data")
        def get_rpa_audit(db_session: DBSession, logger: DDLogger):
            try:
                logger.info("Getting RPA audit")

                return rpa_audit.get_rpa_audit_data(db_session)
            except Exception as e:
                logger.error(f"Error getting RPA audit: {e}")
                raise e

        @self.router.get("/rpa-errors")
        def get_rpa_errors(db_session: DBSession, logger: DDLogger):
            try:
                logger.info("Getting RPA errors")

                return rpa_audit.get_rpa_errors(db_session)
            except Exception as e:
                logger.error(f"Error getting RPA errors: {e}")
                raise e
