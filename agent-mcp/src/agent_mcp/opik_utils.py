import os
import opik
from loguru import logger
from opik.configurator.configure import OpikCOnfigurator


from agent_mcp.config import get_settings

settings = get_settings()

def configure() -> None:
    if settings.OPIK_API_KEY and settings.OPIK_PROJECT:
        try:
            client = OpikCOnfigurator(api_key = settings.OPIK_API_KEY)
            default_workspace = client._get_default_workspace()
        except Exception:
            logger.warning("Default workspace not dound. Setting Workspace to None and enabling interactive mode")
            default_workspace = None
    
        os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT

        try:
            opik.onfigure(
                api_key = settings.OPIK_API_KEY,
                workspace = default_workspace,
                use_local = False,
                force = True
            )
            logger.info(f"Opik COnfigured successfully using workspace {default_workspace}")
        except Exception as e:
            logger.error(e)
            logger.warning("Couldn't configure Opik. There is a probably a problem with the COMET_API_KEY or COMET Config")

    else:
        logger.warning("COMET_API_KEY and COMET_PROJECT are not set.set them to enable prompt monitoring with OPIk")