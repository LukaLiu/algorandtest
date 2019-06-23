import asyncio, time

from simpy.core import Environment, NORMAL


class AsyncIOEnvironment(Environment):
    def __init__(self, loop=None):
        Environment.__init__(self, time.time())
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self._event_task = None

    @property
    def now(self):
        return time.time()

    def schedule(self, event, priority=NORMAL, delay=0):
        # Resume run() if necessary.
        if self._event_task is not None:
            self._event_task.set_result()
            self._event_task = None
        return Environment.schedule(self, event, priority, delay)

    async def run(self):
        while True:
            while self._queue and self._queue[0][0] <= self.now:
                self.step()

            if not self._queue:
                self._event_task = asyncio.Future(loop=self.loop)
                await self._event_task
            else:
                await asyncio.sleep(self._queue[0][0] - self.now)


def clock(env, name, delay, steps=10):
    for i in range(steps):
        yield env.timeout(delay)
        print(f'{name}: {i}')


env = AsyncIOEnvironment()
env.process(clock(env, 'slow', 1))
env.process(clock(env, 'fast', 0.5))
asyncio.get_event_loop().run_until_complete(env.run())