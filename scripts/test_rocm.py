import torch
print(f"Torch Version: {torch.__version__}")
print(f"ROCm Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device Name: {torch.cuda.get_device_name(0)}")
    t = torch.tensor([1, 2, 3]).cuda()
    print(f"Tensor on GPU: {t}")
