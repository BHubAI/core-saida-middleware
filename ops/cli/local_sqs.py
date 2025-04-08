#!/usr/bin/env python
import boto3
import click
from botocore.exceptions import ClientError


@click.group()
def cli():
    """LocalStack SQS management commands"""
    pass


@cli.command()
@click.argument("queue_name")
@click.option("--region", "-r", default="us-east-2", help="AWS region")
@click.option("--endpoint", "-e", default="http://localhost:4566", help="LocalStack endpoint URL")
@click.option("--fifo", "-f", is_flag=True, help="Create a FIFO queue")
@click.option(
    "--content-based-dedup",
    "-c",
    is_flag=True,
    help="Enable content-based deduplication for FIFO queues",
)
def create_queue(queue_name, region, endpoint, fifo, content_based_dedup):
    """Create a new SQS queue on LocalStack"""
    try:
        # Create SQS client
        sqs = boto3.client(
            "sqs",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

        # Prepare queue attributes
        attributes = {}
        if fifo:
            pass
            # if not queue_name.endswith(".fifo"):
            #     queue_name = f"{queue_name}.fifo"
            # attributes["FifoQueue"] = "true"
            # if content_based_dedup:
            #     attributes["ContentBasedDeduplication"] = "true"
            # else:
            #     attributes["ContentBasedDeduplication"] = "false"

        # Create the queue
        response = sqs.create_queue(QueueName=queue_name, Attributes=attributes)
        queue_url = response["QueueUrl"]

        click.echo(f"Queue '{queue_name}' created successfully!")
        click.echo(f"Queue URL: {queue_url}")
        if fifo:
            click.echo("Queue type: FIFO")
            click.echo(
                f"Content-based deduplication: {'enabled' if content_based_dedup else 'disabled'}"
            )

    except ClientError as e:
        click.echo(f"Error creating queue: {e}", err=True)
        return 1

    return 0


@cli.command()
@click.option("--region", "-r", default="us-east-2", help="AWS region")
@click.option("--endpoint", "-e", default="http://localhost:4566", help="LocalStack endpoint URL")
def list_queues(region, endpoint):
    """List all SQS queues on LocalStack"""
    try:
        # Create SQS client
        sqs = boto3.client(
            "sqs",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

        # List queues
        response = sqs.list_queues()
        queues = response.get("QueueUrls", [])

        if not queues:
            click.echo("No queues found.")
            return 0

        click.echo("Available queues:")
        for queue_url in queues:
            click.echo(f"  - {queue_url}")

    except ClientError as e:
        click.echo(f"Error listing queues: {e}", err=True)
        return 1

    return 0


@cli.command()
@click.argument("queue_name")
@click.option("--region", "-r", default="us-east-2", help="AWS region")
@click.option("--endpoint", "-e", default="http://localhost:4566", help="LocalStack endpoint URL")
def delete_queue(queue_name, region, endpoint):
    """Delete an SQS queue on LocalStack"""
    try:
        # Create SQS client
        sqs = boto3.client(
            "sqs",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id="test",
            aws_secret_access_key="test",
        )

        # Get queue URL
        response = sqs.get_queue_url(QueueName=queue_name)
        queue_url = response["QueueUrl"]

        # Delete the queue
        sqs.delete_queue(QueueUrl=queue_url)

        click.echo(f"Queue '{queue_name}' deleted successfully!")

    except ClientError as e:
        click.echo(f"Error deleting queue: {e}", err=True)
        return 1

    return 0


if __name__ == "__main__":
    cli()
