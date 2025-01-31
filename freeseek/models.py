class ModelHandler:
    """
    A handler class for interacting with the FreeseekAPI.
    """

    def __init__(self, api: "FreeseekAPI"):
        """
        Initialize the ModelHandler with a FreeseekAPI instance.

        :param api: An instance of FreeseekAPI.
        """
        self.api = api

    def infer_model(self, model: str, data: dict) -> dict:
        """
        Infer the model with the provided data.

        :param model: The name of the model to infer.
        :param data: The data to be used for inference.
        :return: The inference result as a dictionary.
        """
        try:
            return self.api.infer(model, data)
        except Exception as e:
            # Handle or log the exception as needed
            raise RuntimeError(f"Failed to infer model {model}: {e}")

    def get_model_info(self, model: str) -> dict:
        """
        Get information about the specified model.

        :param model: The name of the model.
        :return: The model information as a dictionary.
        """
        try:
            return self.api.get_model_info(model)
        except Exception as e:
            # Handle or log the exception as needed
            raise RuntimeError(f"Failed to get model info for {model}: {e}")
