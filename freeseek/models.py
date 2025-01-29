class ModelHandler:
    def __init__(self, api: "FreeseekAPI"):
        self.api = api

    def infer_model(self, model: str, data: dict):
        return self.api.infer(model, data)

    def get_model_info(self, model: str):
        return self.api.get_model_info(model)
