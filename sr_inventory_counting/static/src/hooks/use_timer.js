import { onWillStart, useComponent } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export function useTimerCount() {
    const component = useComponent();
    const timerService = useService("timer_count");
    onWillStart(timerService.getServerOffset.bind(component));

    return timerService.createTimer();
}
