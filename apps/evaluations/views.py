"""
Model Evaluation and Academic Benchmarking Views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from database.repositories.evaluation_repository import EvaluationRepository
from database.repositories.audit_repository import AuditRepository
from ai_engine.model_registry import REGISTERED_MODELS
from ai_engine.evaluation import CrossDatasetEvaluator, BENCHMARK_DATASETS

@login_required
def index_view(request):
    """Model evaluation workspace."""
    evaluation_result = None

    if request.method == "POST":
        model_id = request.POST.get("model_id")
        dataset_id = request.POST.get("dataset_id")

        try:
            evaluation_result = CrossDatasetEvaluator.run_benchmark_evaluation(
                model_id=model_id,
                dataset_id=dataset_id,
                user=request.user.username
            )
            # Save evaluation run to MongoDB
            EvaluationRepository.create_evaluation_record(
                model_id=model_id,
                dataset_name=evaluation_result["dataset_name"],
                metrics=evaluation_result["metrics"],
                sample_count=evaluation_result["sample_count"],
                confusion_matrix=evaluation_result["confusion_matrix"],
                labels=evaluation_result["labels"],
                executed_by=request.user.username
            )
            AuditRepository.record_event(
                actor=request.user.username,
                action="MODEL_EVALUATION_EXECUTED",
                metadata={"model_id": model_id, "dataset_id": dataset_id, "accuracy": evaluation_result["metrics"]["accuracy"]},
                ip_address=request.META.get("REMOTE_ADDR")
            )
            messages.success(request, f"Benchmark evaluation completed with Accuracy: {round(evaluation_result['metrics']['accuracy']*100, 1)}%!")
        except Exception as e:
            messages.error(request, f"Evaluation error: {str(e)}")

    past_evaluations = EvaluationRepository.list_recent(limit=10)

    return render(request, "evaluations/index.html", {
        "models": list(REGISTERED_MODELS.values()),
        "datasets": list(BENCHMARK_DATASETS.values()),
        "evaluation": evaluation_result,
        "past_evaluations": past_evaluations,
    })
