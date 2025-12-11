import os
import opik
from loguru import logger
from opik.configurator.configure import OpikConfigurator

from agent_api.config import get_settings

settings = get_settings()


def configure()->None:
    if settings.OPIK_API_KEY and settings.OPIK_PROJECT:
        try:
            client = OpikConfigurator(api_key=settings.OPIK_API_KEY)
            default_workspace = client._get_default_workspace()
        except Exception as e:
            logger.warning(
                "Default Workspace not found. Setting Workspace to None and enabling Interactive mode."
            )
            default_workspace = None
        
        os.environ["OPIK_PROJECT_NAME"] = settings.OPIK_PROJECT
    
        try:
            opik.configure(
                api_key=settings.OPIK_API_KEY,
                workspace=default_workspace,
                use_local=False,
                force = True,
            )

            logger.info(f"Opik configured successfully using workspaces {default_workspace}")

        except Exception as e:
            logger.error(e)
            logger.warning(f"Couldn;t configure Opik.")
        
    else:
        logger.warning("COMET API KEY and COMET_PROJECT are not set. set them enable Opik Monitoring")

            