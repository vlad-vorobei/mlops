# MLOps Train Automation - автоматизоване тренування моделей

Пайплайн тренування на базі **AWS Step Functions** та **GitLab CI**: валідація даних та логування метрик через Lambda, запуск при push у репозиторій.

## Архітектура

- **Step Function** (MLOpsPipeline): два кроки - `ValidateData` → `LogMetrics`.
- **Lambda** `ValidateData`: умовна валідація вхідних даних.
- **Lambda** `LogMetrics`: умовне логування метрик (наприклад, у MLflow).
- **GitLab CI**: job `train-model` викликає `aws stepfunctions start-execution` при push.

---

## 1. Як зібрати архіви .zip для Lambda

Перед першим `terraform apply` потрібно зібрати архіви з Python-файлів Lambda:

```bash
cd terraform/lambda
zip validate.zip validate.py
zip log_metrics.zip log_metrics.py
cd ../..
```

Перевірка:

```bash
ls -la terraform/lambda/*.zip
```

Мають бути файли `validate.zip` та `log_metrics.zip`.

---

## 2. Як розгорнути інфраструктуру через Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Після успішного apply збережіть **ARN Step Function** з виводу:

```text
Outputs:
step_function_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:MLOpsPipeline"
```

Це значення потрібне для змінної GitLab CI `STEP_FUNCTION_ARN`.

---

## 3. Як вручну перевірити Step Function через AWS Console

1. Увійдіть у **AWS Console** → **Step Functions**.
2. Відкрийте state machine **MLOpsPipeline**.
3. Натисніть **Start execution**.
4. У полі **Input** можна ввести JSON, наприклад:
   ```json
   {"source": "manual", "commit": "test"}
   ```
   або залишити `{}`.
5. Натисніть **Start execution** і перегляньте виконання: спочатку **ValidateData**, потім **LogMetrics**. Обидва кроки повинні завершитися успішно.

Перевірка через AWS CLI:

```bash
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:REGION:ACCOUNT:stateMachine:MLOpsPipeline" \
  --name "manual-$(date +%s)" \
  --input '{"source":"cli", "commit":"manual-test"}'
```

---

## 4. Як працює GitLab CI job

- **Файл**: `.gitlab-ci.yml`.
- **Stage**: `train`.
- **Job**: `train-model` - запускає Step Function через `aws stepfunctions start-execution`.
- **Образ**: `amazon/aws-cli:2.15.0` (офіційний AWS CLI).
- **Тригер**: виконується при **push** (rules: `if: $CI_PIPELINE_SOURCE == "push"`).

### Необхідні змінні в GitLab (Settings → CI/CD → Variables)

| Змінна | Тип | Опис |
|--------|-----|------|
| `STEP_FUNCTION_ARN` | Variable (masked) | ARN state machine з виводу `terraform output step_function_arn` |
| `AWS_ACCESS_KEY_ID` | Variable (masked) | Ключ доступу AWS |
| `AWS_SECRET_ACCESS_KEY` | Variable (masked) | Секретний ключ AWS |
| `AWS_DEFAULT_REGION` | Variable | Регіон, напр. `us-east-1` |

---

## 5. Приклад JSON, який передається через CI

GitLab CI передає вхідний JSON у Step Function через параметр `--input`:

```json
{
  "source": "gitlab-ci",
  "commit": "a1b2c3d4"
}
```

- `source` - джерело запуску (`gitlab-ci`).
- `commit` - короткий SHA коміту (`$CI_COMMIT_SHORT_SHA`).

Цей JSON отримує перша Lambda (`ValidateData`) в полі `event`; її результат передається наступній Lambda (`LogMetrics`).

---

## Структура проєкту

```text
mlops-train-automation/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── lambda/
│       ├── validate.py
│       ├── log_metrics.py
│       ├── validate.zip
│       └── log_metrics.zip
├── .gitlab-ci.yml
└── README.md
```
