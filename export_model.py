import torch
import torchvision.models as models


def export_to_torchscript():
    print("MobileNetV2 downloading...")
    model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
    model.eval()

    print("Model tracing...")
    dummy_input = torch.randn(1, 3, 224, 224)

    traced_model = torch.jit.trace(model, dummy_input)

    model_path = "mobilenet_v2.pt"
    traced_model.save(model_path)
    print(f"Model successfully saved in file: {model_path}")


if __name__ == "__main__":
    export_to_torchscript()
