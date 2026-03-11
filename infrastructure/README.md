# EKS + VPC (модульна структура Terraform)

Інфраструктура: VPC (офіційний модуль) та EKS з двома node group-ами (CPU та GPU задачі).

## Структура проєкту

```
infrastructure/
├── main.tf                    # виклик модулів vpc та eks
├── variables.tf
├── outputs.tf
├── terraform.tf               # required_providers, provider aws
├── backend.tf                 # S3 backend
├── terraform.tfvars.example   # приклад змінних (скопіювати в terraform.tfvars)
├── vpc/
│   ├── main.tf                # terraform-aws-modules/vpc/aws
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tf
│   └── backend.tf
├── eks/
│   ├── main.tf                # terraform-aws-modules/eks/aws + data.terraform_remote_state
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tf
│   └── backend.tf
└── README.md
```

## Попередні вимоги

- AWS CLI налаштований (профіль або IAM)
- Terraform >= 1.3.0
- S3 bucket для backend (параметри в `backend.tf`)

## Змінні та tfvars

Кореневі змінні: `cluster_name`, `region` (опис у `variables.tf`).

Приклад значень - у файлі **`terraform.tfvars.example`**. Щоб використати свої значення:

```bash
cp terraform.tfvars.example terraform.tfvars
# Відредагуйте terraform.tfvars (наприклад, cluster_name, region)
```

Запуск з явним файлом змінних:

```bash
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## Використання

```bash
cd infrastructure
terraform init
terraform plan
terraform apply
```

Після успішного apply:

```bash
aws eks --region us-east-1 update-kubeconfig --name <cluster_name>
kubectl get nodes
```

(Підставте свій `cluster_name` або скористайтеся output `configure_kubectl`.)

Мають з’явитися обидві node group-и (cpu_nodes, gpu_nodes).

## Node groups

- **cpu_nodes** - `t3.micro`, label `workload = cpu-tasks`
- **gpu_nodes** - `t3.micro`, label `workload = gpu-tasks` (для реальних GPU можна змінити `instance_types` на g4dn.xlarge)

## terraform_remote_state

Модуль EKS може брати VPC з `data.terraform_remote_state` (backend S3, key `root/terraform.tfstate`). При виклику з кореневого `main.tf` VPC передається напряму з `module.vpc` (`use_remote_state = false`). При окремому запуску з каталогу `eks/` задайте `use_remote_state = true` і не передавайте `vpc_id`/`subnet_ids` - тоді використовується remote state.
