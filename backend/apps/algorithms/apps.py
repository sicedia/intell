from django.apps import AppConfig


class AlgorithmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.algorithms'
    
    def ready(self):
        """Register all algorithms when app is ready."""
        try:
            from .registry import AlgorithmRegistry
            from .demo.top_patent_countries import TopPatentCountriesAlgorithm
            from .demo.top_patent_inventors import TopPatentInventorsAlgorithm
            from .demo.top_patent_applicants import TopPatentApplicantsAlgorithm
            from .demo.patent_evolution import PatentEvolutionAlgorithm
            from .demo.patent_cumulative import PatentCumulativeAlgorithm
            from .demo.patent_trends_cumulative import PatentTrendsCumulativeAlgorithm
            from .demo.patent_forecast import PatentForecastAlgorithm
            from .demo.cpc_treemap import CPCTreemapAlgorithm
            
            registry = AlgorithmRegistry()
            
            # Register all algorithms
            registry.register("top_patent_countries", "1.0", TopPatentCountriesAlgorithm())
            registry.register("top_patent_inventors", "1.0", TopPatentInventorsAlgorithm())
            registry.register("top_patent_applicants", "1.0", TopPatentApplicantsAlgorithm())
            registry.register("patent_evolution", "1.0", PatentEvolutionAlgorithm())
            registry.register("patent_cumulative", "1.0", PatentCumulativeAlgorithm())
            registry.register("patent_trends_cumulative", "1.0", PatentTrendsCumulativeAlgorithm())
            registry.register("patent_forecast", "1.0", PatentForecastAlgorithm())
            registry.register("cpc_treemap", "1.0", CPCTreemapAlgorithm())
        except ImportError as e:
            # Log but don't fail if modules not available
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to register some algorithms: {e}")

