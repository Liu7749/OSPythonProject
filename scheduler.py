from pcb import PCB


class Scheduler:
    """所有调度器的基类"""

    def __init__(self):
        self.ready_queue = []
        self.blocked_queue = []
        self.terminated_processes = []

    def add_process(self, process):
        """添加新进程到就绪队列"""
        if process.state == PCB.READY and process not in self.ready_queue:
            self.ready_queue.append(process)

    def block_process(self, process):
        """将进程移至阻塞队列"""
        if process in self.ready_queue:
            self.ready_queue.remove(process)
        process.state = PCB.BLOCKED
        self.blocked_queue.append(process)

    def unblock_processes(self):
        """检查并解除阻塞完成I/O的进程"""
        still_blocked = []
        for process in self.blocked_queue:
            process.update_io()
            if process.state == PCB.READY:
                self.ready_queue.append(process)
            else:
                still_blocked.append(process)
        self.blocked_queue = still_blocked

    def terminate_process(self, process, current_time):
        """将进程标记为终止状态"""
        if process in self.ready_queue:
            self.ready_queue.remove(process)
        process.state = PCB.TERMINATED
        process.completion_time = current_time
        self.terminated_processes.append(process)

    def get_next_process(self):
        """获取下一个要执行的进程 (子类必须实现)"""
        raise NotImplementedError("子类必须实现get_next_process方法")

    def update_queues(self):
        """更新队列中进程的状态"""
        for process in self.ready_queue:
            process.update_waiting()


class PriorityScheduler(Scheduler):
    """静态优先级调度"""

    def get_next_process(self):
        if not self.ready_queue:
            return None

        # 按静态优先级排序 (数字小 = 优先级高)
        self.ready_queue.sort(key=lambda p: p.static_priority)
        return self.ready_queue[0]


class DynamicPriorityScheduler(Scheduler):
    """动态优先级调度"""

    def __init__(self, aging_factor=3):
        super().__init__()
        self.aging_factor = aging_factor

    def update_queues(self):
        """更新等待时间和动态优先级"""
        super().update_queues()

        # 根据等待时间更新优先级
        for process in self.ready_queue:
            process.update_dynamic_priority(self.aging_factor)

    def get_next_process(self):
        if not self.ready_queue:
            return None

        # 按动态优先级排序
        self.ready_queue.sort(key=lambda p: p.dynamic_priority)
        return self.ready_queue[0]


class RoundRobinScheduler(Scheduler):
    """时间片轮转调度"""

    def __init__(self, time_quantum=2):
        super().__init__()
        self.time_quantum = time_quantum
        self.current_process = None
        self.time_used = 0

    def get_next_process(self):
        if not self.ready_queue:
            self.current_process = None
            self.time_used = 0
            return None

        # 如果当前进程不在就绪队列中或时间片用完，选择新进程
        if (self.current_process is None or
                self.current_process not in self.ready_queue or
                self.time_used >= self.time_quantum):

            # 如果当前进程仍在就绪队列中，移至队列末尾
            if self.current_process in self.ready_queue:
                self.ready_queue.remove(self.current_process)
                self.ready_queue.append(self.current_process)

            # 选择队首进程
            self.current_process = self.ready_queue[0]
            self.time_used = 0

        self.time_used += 1
        return self.current_process


class SJFScheduler(Scheduler):
    """短作业优先调度"""

    def get_next_process(self):
        if not self.ready_queue:
            return None

        # 按总执行时间排序
        self.ready_queue.sort(key=lambda p: p.burst_time)
        return self.ready_queue[0]


class SRTFScheduler(Scheduler):
    """短剩余时间优先调度"""

    def get_next_process(self):
        if not self.ready_queue:
            return None

        # 按剩余执行时间排序
        self.ready_queue.sort(key=lambda p: p.remaining_time)
        return self.ready_queue[0]


class MLFQScheduler:
    """多级反馈队列调度"""

    def __init__(self, time_quantum=2, num_queues=3):
        self.queues = [[] for _ in range(num_queues)]  # 多级队列
        self.blocked_queue = []
        self.terminated_processes = []
        self.num_queues = num_queues
        self.base_quantum = time_quantum
        self.current_process = None
        self.time_used = 0
        self.current_level = 0

    @property
    def ready_queue(self):
        """所有就绪进程的平面列表"""
        result = []
        for queue in self.queues:
            result.extend(queue)
        return result

    @ready_queue.setter
    def ready_queue(self, value):
        """处理队列清空操作"""
        if not value:
            for i in range(self.num_queues):
                self.queues[i] = []

    def add_process(self, process):
        """添加新进程到最高优先级队列"""
        if process.state == PCB.READY:
            # 确保进程不在任何队列中
            for queue in self.queues:
                if process in queue:
                    return
            self.queues[0].append(process)

    def block_process(self, process):
        """将进程移至阻塞队列"""
        # 从当前所在队列移除
        for level in range(self.num_queues):
            if process in self.queues[level]:
                self.queues[level].remove(process)
                break

        # 如果是当前执行的进程，重置状态
        if process == self.current_process:
            self.current_process = None
            self.time_used = 0

        process.state = PCB.BLOCKED
        self.blocked_queue.append(process)

    def unblock_processes(self):
        """处理阻塞队列中的进程"""
        still_blocked = []
        for process in self.blocked_queue:
            process.update_io()
            if process.state == PCB.READY:
                # I/O完成后进程回到最高优先级队列
                self.queues[0].append(process)
            else:
                still_blocked.append(process)
        self.blocked_queue = still_blocked

    def terminate_process(self, process, current_time):
        """终止进程"""
        # 从所有队列中查找并移除
        for level in range(self.num_queues):
            if process in self.queues[level]:
                self.queues[level].remove(process)
                break

        # 如果是当前进程，重置状态
        if process == self.current_process:
            self.current_process = None
            self.time_used = 0

        process.state = PCB.TERMINATED
        process.completion_time = current_time
        self.terminated_processes.append(process)

    def update_queues(self):
        """更新所有队列中进程的等待时间"""
        for level in range(self.num_queues):
            for process in self.queues[level]:
                process.update_waiting()

    def get_next_process(self):
        """获取下一个要执行的进程"""
        # 检查是否有进程存在
        if not any(self.queues):
            self.current_process = None
            self.time_used = 0
            return None

        # 当前级别的时间片大小
        current_quantum = self.base_quantum * (2 ** self.current_level)

        # 如果当前进程时间片用完或不存在
        if (self.current_process is None or self.time_used >= current_quantum):
            # 如果有当前进程且时间片用完，降级
            if (self.current_process is not None and self.time_used >= current_quantum):
                # 找到进程所在队列并降级
                for level in range(self.num_queues):
                    if self.current_process in self.queues[level]:
                        self.queues[level].remove(self.current_process)
                        next_level = min(level + 1, self.num_queues - 1)
                        self.queues[next_level].append(self.current_process)
                        break

            # 重置状态并从最高优先级队列开始查找新进程
            self.current_process = None
            self.time_used = 0

            for level in range(self.num_queues):
                if self.queues[level]:
                    self.current_process = self.queues[level][0]
                    self.current_level = level
                    break

        # 如果找到进程，增加已用时间
        if self.current_process:
            self.time_used += 1

        return self.current_process