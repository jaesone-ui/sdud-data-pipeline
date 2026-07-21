.PHONY: up infrastructure start stop restart destroy

up: infrastructure start
infrastructure:
	cd terraform && terraform init
	cd terraform && terraform apply -auto-approve
start:
	astro dev start
stop:
	astro dev stop
restart:
	astro dev restart
destroy:
	cd terraform && terraform destroy -auto-approve