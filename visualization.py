import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

class SchedulerVisualizer:
    """Visualization for process scheduling simulation."""
    
    def __init__(self, simulator):
        self.simulator = simulator
        self.processes = simulator.processes
        self.execution_log = simulator.execution_log
    
    def visualize_gantt_chart(self, title="Process Scheduling Simulation"):
        """Create a Gantt chart visualization of process execution."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Define colors for different process states
        state_colors = {
            'run': 'green',
            'blocked': 'red',
            'ready': 'yellow',
            'idle': 'lightgray'
        }
        
        # Create process colors dictionary
        process_colors = {}
        for i, process in enumerate(self.processes):
            if process.color:
                process_colors[process.pid] = process.color
            else:
                # Generate a distinct color for each process
                process_colors[process.pid] = plt.cm.tab10(i % 10)
        
        # Extract continuous execution periods for each process
        execution_periods = {}
        for i in range(len(self.execution_log) - 1):
            time, pid, status = self.execution_log[i]
            next_time = self.execution_log[i + 1][0]
            
            if status == "run":
                if pid not in execution_periods:
                    execution_periods[pid] = []
                execution_periods[pid].append((time, next_time))
        
        # Add last execution period if needed
        if len(self.execution_log) > 0:
            last_time, last_pid, last_status = self.execution_log[-1]
            if last_status == "run" and last_pid in execution_periods:
                execution_periods[last_pid].append((last_time, last_time + 1))
        
        # Plot execution periods
        y_ticks = []
        y_labels = []
        
        for i, process in enumerate(self.processes):
            y_pos = len(self.processes) - i
            y_ticks.append(y_pos)
            y_labels.append(f"P{process.pid}")
            
            if process.pid in execution_periods:
                for start, end in execution_periods[process.pid]:
                    ax.barh(y_pos, end - start, left=start, height=0.5, 
                           color=process_colors[process.pid], alpha=0.75)
        
        # Plot I/O periods
        for process in self.processes:
            y_pos = len(self.processes) - self.processes.index(process)
            
            for start, end, status in process.execution_history:
                if status == "blocked":
                    ax.barh(y_pos, end - start, left=start, height=0.5,
                           color='red', alpha=0.6)
        
        # Set chart properties
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.set_xlabel("Time")
        ax.set_ylabel("Process")
        ax.grid(True, axis='x', linestyle='--', alpha=0.7)
        ax.set_title(title)
        
        # Add legend for process states
        legend_handles = [
            patches.Patch(color='green', alpha=0.75, label='Running'),
            patches.Patch(color='red', alpha=0.6, label='I/O Blocked')
        ]
        ax.legend(handles=legend_handles, loc='upper right')
        
        # Add statistics text
        stats_text = "Process Statistics:\n"
        for process in self.processes:
            stats_text += f"P{process.pid}: Turnaround={process.turnaround_time}, Waiting={process.waiting_time}\n"
        
        plt.figtext(0.02, 0.02, stats_text, fontsize=9, 
                   bbox=dict(facecolor='white', alpha=0.8))
        
        plt.tight_layout()
        return fig