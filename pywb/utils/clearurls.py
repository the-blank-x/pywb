import re
import typing
from urllib.parse import unquote
from dataclasses import dataclass

@dataclass
class Provider:
    name: str
    url_pattern: typing.Union[str, re.Pattern]
    complete_provider: bool
    rules: list[typing.Union[str, re.Pattern]]
    raw_rules: list[typing.Union[str, re.Pattern]]
    referral_marketing: list[typing.Union[str, re.Pattern]]
    exceptions: list[typing.Union[str, re.Pattern]]
    redirections: list[typing.Union[str, re.Pattern]]
    force_redirection: bool

    @classmethod
    def from_json(cls, name: str, js: dict) -> "Provider":
        return cls(
            name,
            js["urlPattern"],
            js.get("completeProvider") or False,
            js.get("rules") or [],
            js.get("rawRules") or [],
            js.get("referralMarketing") or [],
            js.get("exceptions") or [],
            js.get("redirections") or [],
            js.get("forceRedirection") or False,
        )

    def clean(self, url: str, allow_referral_marketing: bool) -> str:
        self._compile(False)
        if not self.url_pattern.search(url) or any(exception.search(url) for exception in self.exceptions):
            return url

        self._compile(True)
        for redirection in self.redirections:
            match = redirection.search(url)
            if match:
                return unquote(match.group(1))

        for raw_rule in self.raw_rules:
            url = raw_rule.sub("", url)
        for rule in self.rules:
            url = rule.sub("", url)
        if not allow_referral_marketing:
            for rule in self.referral_marketing:
                url = rule.sub("", url)
        return url

    def _compile(self, full: bool):
        if isinstance(self.url_pattern, str):
            self.url_pattern = re.compile(self.url_pattern)
        for index, exception in enumerate(self.exceptions):
            if isinstance(exception, str):
                self.exceptions[index] = re.compile(exception)

        if not full:
            return

        for index, rule in enumerate(self.rules):
            if isinstance(rule, str):
                rule = r"(?:&amp;|[/?#&])(?:" + rule + r"=[^&]*)"
                self.rules[index] = re.compile(rule)

        for index, raw_rule in enumerate(self.raw_rules):
            if isinstance(raw_rule, str):
                self.raw_rules[index] = re.compile(raw_rule)

        for index, rule in enumerate(self.referral_marketing):
            if isinstance(rule, str):
                rule = r"(?:&amp;|[/?#&])(?:" + rule + r"=[^&]*)"
                self.referral_marketing[index] = re.compile(rule)

        for index, redirection in enumerate(self.redirections):
            if isinstance(redirection, str):
                self.redirections[index] = re.compile(redirection)


def parse_providers(js: dict) -> list[Provider]:
    return [Provider.from_json(key, value) for key, value in js["providers"].items()]

def clean(providers: list[Provider], url: str, allow_referral_marketing: bool) -> str:
    before = after = url

    while True:
        for provider in providers:
            if provider.complete_provider:
                continue

            after = provider.clean(after, allow_referral_marketing)

        if before == after:
            break
        before = after

    return after
