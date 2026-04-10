from __future__ import annotations

try:
    from workers import WorkerEntrypoint
except ImportError:  # pragma: no cover - local fallback

    class WorkerEntrypoint:  # type: ignore[override]
        pass

import app.dependencies as dependencies_module
import app.main as main_module

_app = None


def _worker_app(env) -> object:
    global _app
    if _app is None:
        _app = main_module.create_app(env)
    else:
        _app.state.container = dependencies_module.build_container(env)
    return _app


class Default(WorkerEntrypoint):
    async def fetch(self, request):  # pragma: no cover - exercised in Cloudflare runtime
        try:
            import asgi
        except ImportError as exc:
            raise RuntimeError("Cloudflare ASGI adapter topilmadi") from exc

        app = _worker_app(self.env)
        return await asgi.fetch(app, request, self.env, self.ctx)

    async def scheduled(self, controller, env, ctx):  # pragma: no cover - exercised in Cloudflare runtime
        app = _worker_app(env)
        await app.state.container.scheduler_service.run_for_cron(getattr(controller, "cron", None))
