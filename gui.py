import tkinter as tk
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
from pcb import PCB
from scheduler import PriorityScheduler, DynamicPriorityScheduler, RoundRobinScheduler, SJFScheduler, SRTFScheduler, \
    MLFQScheduler
from simulator import TaskSimulator


class SimulatorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("任务调度模拟器")
        # 增加窗口高度，确保统计数据完全显示
        self.root.geometry("1200x780")

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用于显示中文
        plt.rcParams['axes.unicode_minus'] = False  # 用于显示负号

        # 初始化变量
        self.schedulers = {
            "优先级调度": PriorityScheduler(),
            "动态优先级调度": DynamicPriorityScheduler(),
            "时间片轮转": RoundRobinScheduler(time_quantum=2),
            "短作业优先(SJF)": SJFScheduler(),
            "短剩余时间优先(SRTF)": SRTFScheduler(),
            "多级反馈队列": MLFQScheduler(time_quantum=2, num_queues=3)
        }
        self.selected_scheduler = tk.StringVar(value="优先级调度")
        self.max_time = tk.IntVar(value=50)
        self.time_quantum = tk.IntVar(value=2)
        self.num_processes = tk.IntVar(value=5)
        self.simulator = TaskSimulator(self.schedulers[self.selected_scheduler.get()])

        # 创建主框架
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 控制面板
        control_panel = ttk.LabelFrame(main_frame, text="控制面板", padding="10")
        control_panel.pack(fill=tk.X, padx=10, pady=5)

        # 调度算法选择
        ttk.Label(control_panel, text="调度算法:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        scheduler_combo = ttk.Combobox(control_panel, textvariable=self.selected_scheduler,
                                       values=list(self.schedulers.keys()),
                                       state="readonly")
        scheduler_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        scheduler_combo.bind("<<ComboboxSelected>>", self.on_scheduler_changed)

        # 时间片长度
        ttk.Label(control_panel, text="时间片长度:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        quantum_entry = ttk.Entry(control_panel, textvariable=self.time_quantum, width=5)
        quantum_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # 最大运行时间
        ttk.Label(control_panel, text="最大运行时间:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        max_time_entry = ttk.Entry(control_panel, textvariable=self.max_time, width=5)
        max_time_entry.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        # 进程数量
        ttk.Label(control_panel, text="进程数量:").grid(row=0, column=6, sticky=tk.W, padx=5, pady=5)
        num_proc_entry = ttk.Entry(control_panel, textvariable=self.num_processes, width=5)
        num_proc_entry.grid(row=0, column=7, sticky=tk.W, padx=5, pady=5)

        # 按钮
        button_frame = ttk.Frame(control_panel)
        button_frame.grid(row=1, column=0, columnspan=8, pady=5)

        ttk.Button(button_frame, text="生成进程", command=self.generate_processes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="运行模拟", command=self.run_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清除", command=self.clear).pack(side=tk.LEFT, padx=5)

        # 进程列表 - 减少高度以留出更多空间给统计数据
        process_frame = ttk.LabelFrame(main_frame, text="进程列表", padding="10")
        process_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建进程表格 - 设置固定高度
        columns = ("进程ID", "优先级", "执行时间", "I/O时间", "到达时间")
        self.process_table = ttk.Treeview(process_frame, columns=columns, show="headings", height=6)

        # 设置列标题
        for col in columns:
            self.process_table.heading(col, text=col)
            self.process_table.column(col, width=100, anchor=tk.CENTER)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(process_frame, orient=tk.VERTICAL, command=self.process_table.yview)
        self.process_table.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.process_table.pack(fill=tk.BOTH, expand=True)

        # 创建可视化区域 - 减少高度
        viz_frame = ttk.LabelFrame(main_frame, text="模拟时间轴", padding="10")
        viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建matplotlib图表 - 减小图表高度
        self.figure = Figure(figsize=(12, 3.2), dpi=100)  # 减小高度
        self.plot = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 统计数据区域 - 增加高度以确保完全显示
        stats_frame = ttk.LabelFrame(main_frame, text="统计数据", padding="10")
        stats_frame.pack(fill=tk.BOTH, padx=10, pady=5)

        # 增加统计数据文本框的高度
        self.stats_text = tk.Text(stats_frame, height=5, width=70)
        self.stats_text.pack(fill=tk.BOTH, expand=True)

        # 初始化默认统计数据
        self.reset_statistics()

    def on_scheduler_changed(self, event):
        """处理调度算法变更"""
        scheduler_name = self.selected_scheduler.get()

        # 更新时间片设置
        if scheduler_name == "时间片轮转":
            self.schedulers[scheduler_name] = RoundRobinScheduler(time_quantum=self.time_quantum.get())
        elif scheduler_name == "多级反馈队列":
            self.schedulers[scheduler_name] = MLFQScheduler(time_quantum=self.time_quantum.get(), num_queues=3)

        # 更新模拟器
        self.simulator = TaskSimulator(self.schedulers[scheduler_name])

    def generate_processes(self):
        """生成随机进程"""
        # 创建新模拟器实例
        self.simulator = TaskSimulator(self.schedulers[self.selected_scheduler.get()])

        # 生成指定数量的随机进程
        self.simulator.create_random_processes(self.num_processes.get())

        # 更新进程表格
        self.update_process_table()

        # 重置统计信息
        self.reset_statistics()

        # 清空图表
        self.plot.clear()
        self.canvas.draw()

    def update_process_table(self):
        """更新进程表格显示"""
        # 清空表格
        for item in self.process_table.get_children():
            self.process_table.delete(item)

        # 添加进程到表格
        for process in self.simulator.processes:
            io_str = ", ".join([f"{t}:{d}" for t, d in process.io_times.items()])
            self.process_table.insert("", tk.END, values=(
                process.pid,
                process.static_priority,
                process.burst_time,
                io_str,
                process.arrival_time
            ))

    def run_simulation(self):
        """运行模拟"""
        # 根据选择更新调度器
        scheduler_name = self.selected_scheduler.get()
        if scheduler_name == "时间片轮转":
            self.schedulers[scheduler_name] = RoundRobinScheduler(time_quantum=self.time_quantum.get())
        elif scheduler_name == "多级反馈队列":
            self.schedulers[scheduler_name] = MLFQScheduler(time_quantum=self.time_quantum.get(), num_queues=3)

        # 创建新模拟器，但保留现有进程
        self.simulator = TaskSimulator(self.schedulers[scheduler_name])

        # 如果没有进程，先生成进程
        if not hasattr(self, 'processes') or not self.simulator.processes:
            self.generate_processes()
        else:
            # 保留现有进程
            processes_backup = self.simulator.processes.copy()
            self.simulator.processes = processes_backup

        # 运行模拟
        try:
            self.simulator.run_simulation(self.max_time.get())
            print(f"模拟完成: {scheduler_name}, 执行历史记录: {len(self.simulator.execution_history)}")

            # 更新可视化
            self.update_visualization()

            # 更新统计数据
            self.update_statistics()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"模拟过程发生错误: {e}")

            # 即使发生错误也尝试更新统计和可视化
            self.update_statistics()
            self.update_visualization()

    def update_visualization(self):
        """更新可视化视图"""
        self.plot.clear()

        # 创建甘特图
        y_ticks = []
        y_labels = []

        # 按PID排序进程以保持一致的显示
        sorted_processes = sorted(self.simulator.processes, key=lambda p: p.pid)

        for i, process in enumerate(sorted_processes):
            y_pos = i + 1
            y_ticks.append(y_pos)
            y_labels.append(f"P{process.pid}")

            if not process.execution_history:
                # 为没有执行历史的进程添加标记
                self.plot.text(5, y_pos, f"未执行 (优先级:{process.static_priority}, 到达时间:{process.arrival_time})",
                               ha='left', va='center', color='red', fontsize=8)

            # 绘制执行时段
            for start, end in process.execution_history:
                self.plot.barh(y_pos, end - start, left=start, height=0.5,
                               color=process.color, alpha=0.8, edgecolor='black')

            # 绘制I/O时段
            io_shown = set()  # 避免重复显示同一时间点的I/O
            for io_time, io_duration in process.io_times.items():
                # 只考虑已执行过的I/O
                if io_time < process.executed_time and io_time not in io_shown:
                    # 查找此I/O操作可能的开始时间
                    io_start = None
                    for start, end in process.execution_history:
                        if start <= io_time < end:
                            io_start = io_time + 1  # I/O在执行点之后开始
                            break

                    if io_start is not None:
                        self.plot.barh(y_pos, io_duration, left=io_start, height=0.3,
                                       color='gray', alpha=0.6, edgecolor='black', hatch='///')

                        # 添加I/O标签
                        self.plot.text(io_start + io_duration / 2, y_pos, 'I/O',
                                       ha='center', va='center', color='black', fontsize=8)
                        io_shown.add(io_time)

        # 设置图表属性
        self.plot.set_yticks(y_ticks)
        self.plot.set_yticklabels(y_labels)
        self.plot.set_xlabel('时间单位')
        self.plot.set_title(f'进程执行时间轴 ({self.selected_scheduler.get()})')
        self.plot.grid(axis='x', linestyle='--', alpha=0.7)

        # 设置x轴限制
        max_time = max([end for p in sorted_processes for _, end in p.execution_history], default=0)
        if max_time == 0:
            max_time = self.simulator.current_time

        self.plot.set_xlim(0, max(max_time + 1, self.max_time.get()))

        self.figure.tight_layout()
        self.canvas.draw()

    def reset_statistics(self):
        """重置统计数据显示为默认值"""
        self.stats_text.delete(1.0, tk.END)
        default_stats = (f"平均等待时间: 0.00 时间单位\n"
                         f"平均周转时间: 0.00 时间单位\n"
                         f"平均响应时间: 0.00 时间单位\n"
                         f"调度算法: {self.selected_scheduler.get()}\n"
                         f"完成进程数: 0/{self.num_processes.get()}")
        self.stats_text.insert(tk.END, default_stats)

    def update_statistics(self):
        """更新统计数据"""
        # 完全清除文本框内容
        self.stats_text.delete(1.0, tk.END)

        # 计算统计指标
        total_waiting_time = 0
        total_turnaround_time = 0
        total_response_time = 0
        completed_count = 0

        # 计算各项指标
        for process in self.simulator.processes:
            if process.state == PCB.TERMINATED:  # 仅考虑已完成的进程
                completed_count += 1
                turnaround_time = process.completion_time - process.arrival_time
                total_turnaround_time += turnaround_time
                total_waiting_time += process.waiting_time

                # 响应时间是从到达到首次执行的时间
                if process.execution_history:
                    first_exec_time = process.execution_history[0][0]
                    response_time = first_exec_time - process.arrival_time
                    total_response_time += response_time

        # 计算平均值 - 避免除零错误
        if completed_count > 0:
            avg_waiting = total_waiting_time / completed_count
            avg_turnaround = total_turnaround_time / completed_count
            avg_response = total_response_time / completed_count
        else:
            avg_waiting = avg_turnaround = avg_response = 0

        # 显示统计结果
        stats_text = (f"平均等待时间: {avg_waiting:.2f} 时间单位\n"
                      f"平均周转时间: {avg_turnaround:.2f} 时间单位\n"
                      f"平均响应时间: {avg_response:.2f} 时间单位\n"
                      f"调度算法: {self.selected_scheduler.get()}\n"
                      f"完成进程数: {completed_count}/{len(self.simulator.processes)}")

        self.stats_text.insert(tk.END, stats_text)

    def clear(self):
        """清空所有显示"""
        # 清空进程表格
        for item in self.process_table.get_children():
            self.process_table.delete(item)

        # 清空图表
        self.plot.clear()
        self.canvas.draw()

        # 清空统计数据
        self.stats_text.delete(1.0, tk.END)

        # 重置模拟器
        self.simulator = TaskSimulator(self.schedulers[self.selected_scheduler.get()])