output "cluster_name" {
  value = module.eks.cluster_name
}

output "ecr_backend_url" {
  value = aws_ecr_repository.backend.repository_url
}

output "ecr_frontend_url" {
  value = aws_ecr_repository.frontend.repository_url
}

output "rds_endpoint" {
  value = aws_db_instance.postgres.address
}

output "rds_master_secret_arn" {
  value = aws_db_instance.postgres.master_user_secret[0].secret_arn
}
