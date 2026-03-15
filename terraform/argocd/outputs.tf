output "namespace" {
  value = kubernetes_namespace.infra_tools.metadata[0].name
}

output "argocd_server_port_forward" {
  value = "kubectl port-forward svc/argocd-server -n ${var.namespace} 8080:443"
}
