resource "kubernetes_namespace" "infra_tools" {
  metadata {
    name = var.namespace
  }
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  version    = var.argocd_chart_version
  namespace  = kubernetes_namespace.infra_tools.metadata[0].name

  values = [
    file("${path.module}/values/argocd-values.yaml")
  ]

  wait    = false
  timeout = 600

  depends_on = [kubernetes_namespace.infra_tools]
}
