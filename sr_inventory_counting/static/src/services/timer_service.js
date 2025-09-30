import { registry } from "@web/core/registry";

import { TimerCountReactive } from "@sr_inventory_counting/models/timer_reactive";

export const timerCountService = {
    start(env) {
        let serverOffset = null;
        let timer;
        return {
            createTimer() {
                timer = new TimerCountReactive(env);
                return timer;
            },
            async getServerOffset() {
                if (serverOffset == null) {
                    const serverTime = await timer.getServerTime();
                    timer.computeOffset(serverTime);
                    serverOffset = timer.serverOffset;
                }
                return serverOffset;
            },
        };
    },
};

registry.category("services").add("timer_count", timerCountService);
