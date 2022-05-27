from funance.scrape.driver import create_driver
from .vanguard import Vanguard
from .tda import Tda


class UnsupportedProviderException(Exception):
    pass


class ProviderFactory:
    providers = {
        'vanguard': Vanguard,
        'tda': Tda
    }

    def get_supported_providers(self):
        return self.providers.keys()

    def get_provider(self, provider_name, existing_session=False):
        provider_class = self.providers.get(provider_name)
        if provider_class is None:
            supported_providers = ', '.join(self.get_supported_providers())
            raise UnsupportedProviderException(f"provider must be one of {supported_providers}")

        detached = not existing_session
        driver = create_driver(session=existing_session, detached=detached)

        return provider_class(driver)
