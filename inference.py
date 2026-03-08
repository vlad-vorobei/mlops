import argparse
import torch
import urllib.request
import json
from PIL import Image
from torchvision import transforms


def load_imagenet_labels():
    """Automatically downloads ImageNet class names."""
    url = "https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json"
    try:
        with urllib.request.urlopen(url) as response:
            labels = json.loads(response.read())
        return labels
    except Exception as e:
        print(f"Error loading labels: {e}")
        return [f"Class {i}" for i in range(1000)]


def predict(image_path, model_path):
    model = torch.jit.load(model_path)
    model.eval()

    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Failed to open image {image_path}: {e}")
        return

    input_tensor = preprocess(image)
    input_batch = input_tensor.unsqueeze(0)

    with torch.no_grad():
        output = model(input_batch)

    probabilities = torch.nn.functional.softmax(output[0], dim=0)

    top3_prob, top3_catid = torch.topk(probabilities, 3)
    labels = load_imagenet_labels()

    print(f"\nResults for: {image_path}")
    print("-" * 30)
    for i in range(top3_prob.size(0)):
        score = top3_prob[i].item()
        category = labels[top3_catid[i].item()]
        print(f"{i + 1}. {category} (Probability: {score:.4f})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Image classification inference")
    parser.add_argument("image", help="Path to the input image (e.g., cat.jpg)")
    parser.add_argument("--model", default="mobilenet_v2.pt", help="Path to the TorchScript model")
    args = parser.parse_args()

    predict(args.image, args.model)