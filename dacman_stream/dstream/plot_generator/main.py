import os
import sys
import argparse
import numpy as np
from experiment import Experiment, AggregateMethod
from redis_stat_generator import RedisStatGenerator
from plot_classes.line_plot import LinePlot
from plot_classes.bar_plot import BarPlot
from plot_classes.box_plot import BoxPlot
import settings as _settings


def tput_redis_benchmark_bar_set_get(experiment_dir):
    # Figure 4
    client_num = [64]
    data_sizes = ['1 KB', '50 KB', '100 KB', '1 MB', '10 MB']

    redis_stat_gen = RedisStatGenerator()

    avg_clients_cmds, std_clients_cmds, all_xtick_labels = redis_stat_gen.compare_clients_num(
        os.path.join(
            experiment_dir,
            "redis_benchmark_results",
            "n_1000"
        )
    )

    client_num_str = "c_%d" % client_num[0]

    clients_avg_set_vals = []
    clients_avg_get_vals = []
    clients_std_set_vals = []
    clients_std_get_vals = []
    for i in range(len(avg_clients_cmds)):
        avg_cli_num, avg_cli_dict = avg_clients_cmds[i]
        std_cli_num, std_cli_dict = std_clients_cmds[i]
        if avg_cli_num != client_num_str:
            continue

        cli_avg_set_val_list = []
        cli_avg_get_val_list = []
        cli_std_set_val_list = []
        cli_std_get_val_list = []
        for j, v in enumerate(all_xtick_labels):
            if v in data_sizes:
                cli_avg_set_val_list.append(avg_cli_dict['SET'][j])
                cli_avg_get_val_list.append(avg_cli_dict['GET'][j])
                cli_std_set_val_list.append(std_cli_dict['SET'][j])
                cli_std_get_val_list.append(std_cli_dict['GET'][j])
        clients_avg_set_vals.append(cli_avg_set_val_list)
        clients_avg_get_vals.append(cli_avg_get_val_list)
        clients_std_set_vals.append(cli_std_set_val_list)
        clients_std_get_vals.append(cli_std_get_val_list)
    
    bar_plot = BarPlot(plot_filename="redis_benchmark_tput_bar_c_64_datasize_set_get",
                       xlabel="Data-sizes",
                       ylabel="Throughput\n(requests/s)",
                       legend_loc="best", ylim_top=35000)

    bar_plot.plot(
        [clients_avg_set_vals[0],
        clients_avg_get_vals[0]],
        data_sizes,
        rotation="vertical",
        legends=['SET', 'GET'],
        std_arrs=[clients_std_set_vals[0]
        ,clients_std_get_vals[0]])


def tput_redis_benchmark_clients_line_set_get(experiment_dir):
    # Figure 5
    client_num = [1, 64, 128, 256, 512]
    data_sizes = ['1 KB', '50 KB', '100 KB', '500 KB', '1 MB']

    redis_stat_gen = RedisStatGenerator()

    clients_redis_res, _, all_xtick_labels = redis_stat_gen.compare_clients_num(
        os.path.join(
            experiment_dir,
            "redis_benchmark_results",
            "n_1000"
        )
    )

    clients_set_vals = []
    clients_get_vals = []
    for cli_num, cli_dict in clients_redis_res:
        cli_set_val_list = []
        cli_get_val_list = []
        for i, v in enumerate(all_xtick_labels):
            if v in data_sizes:
                cli_set_val_list.append(cli_dict['SET'][i])
                cli_get_val_list.append(cli_dict['GET'][i])
        clients_set_vals.append(cli_set_val_list)
        clients_get_vals.append(cli_get_val_list)

    client_num_str = [str(n) for n in client_num]
    
    line_plot = LinePlot(
        plot_filename="redis_benchmark_tput_line_clients_datasize_set",
        xlabel="Data-sizes",
        ylabel="Throughput\n(requests/s)",
        legend_loc="best"
    )

    line_plot.plot(
        clients_set_vals,
        data_sizes, "--o",
        legends=client_num_str,
        rotation="vertical",
        ncol=3)

    line_plot = LinePlot(
        plot_filename="redis_benchmark_tput_line_clients_datasize_get",
        xlabel="Data-sizes",
        ylabel="Throughput\n(requests/s)",
        legend_loc="best"
    )

    line_plot.plot(
        clients_get_vals,
        data_sizes, "--o",
        legends=client_num_str,
        rotation="vertical",
        ncol=3)


def tput_latency_3_apps_local_live_buffered_w_1(experiment_dir):
    # Figure 6 A
    apps = ["als", "flux_msip", "flux_mscp"]
    data_sizes = ["10mb", "105b", "105b"]
    sources = [1, 2, 2]
    workers = [1]

    xtick_labels = ["Real-time", "Buffered"]

    apps_tput_avg_values = []
    apps_tput_std_values = []
    var1 = "normalized_throughput"
    #std_var = "std_throughput"

    apps_latency_avg_values = []
    apps_latency_std_values = []
    var2 = "avg_event_time_latency"
    #std_var = "std_event_time_latency"
    for i in range(len(apps)):
        exp_local_live = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=True, is_buffered=False)
        exp_local_buffered = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=True, is_buffered=True)

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_local_live.add_setup(sources[i], workers[j])
            exp_local_buffered.add_setup(sources[i], workers[j])

        exp_local_live.process()
        exp_local_buffered.process()

        apps_tput_avg_values.append(exp_local_live.get_agg_results(var1) +
            exp_local_buffered.get_agg_results(var1))
        apps_tput_std_values.append(exp_local_live.get_agg_results(var1, AggregateMethod.STD) + 
            exp_local_buffered.get_agg_results(var1, AggregateMethod.STD))
        #apps_var_std_values.append(exp_local_live.get_agg_results(std_var) + 
        #    exp_local_buffered.get_agg_results(std_var))

        apps_latency_avg_values.append(exp_local_live.get_agg_results(var2) +
            exp_local_buffered.get_agg_results(var2))
        apps_latency_std_values.append(exp_local_live.get_agg_results(var2, AggregateMethod.STD) + 
            exp_local_buffered.get_agg_results(var2, AggregateMethod.STD))

    bar_plot = BarPlot(plot_filename="tput_3_apps_local_live_buffered_w_1",
                       xlabel="Processing Strategy",
                       ylabel="Throughput\n(tasks/s)",
                       ylim_top=2200, legend_size=18)

    bar_plot.plot(
        apps_tput_avg_values,
        xtick_labels,
        legends=["ImageAnalysis", "MovingAverage", "ChangeDetection"],
        std_arrs=apps_tput_std_values, ncol=2, display_val=True)

    bar_plot = BarPlot(plot_filename="latency_3_apps_local_live_buffered_w_1",
                       xlabel="Processing Strategy",
                       ylabel="Latency (s)",
                       ylim_top=2800, legend_size=18)

    bar_plot.plot(
        apps_latency_avg_values,
        xtick_labels,
        legends=["ImageAnalysis", "MovingAverage", "ChangeDetection"],
        std_arrs=apps_latency_std_values, ncol=2, display_val=True)


def tput_3_apps_2_modes_buffered_w_1_64(experiment_dir):
    # Figure 7 Throughput of apps with buffered data
    # comparing performance between local and cluster
    # modes from 1 to 64 workers
    apps = ["als", "flux_msip", "flux_mscp"]
    data_sizes = ["10mb", "105b", "105b"]
    sources = [1, 2, 2]
    workers = [1, 4, 8, 16, 32, 64]

    xtick_labels = [str(w) for w in workers]

    var = "normalized_throughput"
    for i in range(len(apps)):
        exp_local = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=True, is_buffered=True)
        exp_cori = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=False, is_buffered=True)

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_local.add_setup(sources[i], workers[j])
            exp_cori.add_setup(sources[i], workers[j])

        exp_local.process()
        exp_cori.process()

        box_plot = BoxPlot(plot_filename="tput_%s_2_modes_buffered_w_1_64" % apps[i],
                           xlabel="Number of Workers",
                           ylabel="Throughput\n(tasks/s)")

        box_plot.plot(
            [exp_local.get_agg_results(var),
            exp_cori.get_agg_results(var)],
            xtick_labels,
            legends=["ImageAnalysis", "MovingAverage", "ChangeDetection"]
        )


def tput_2_apps_2_modes_live_w_1_64(experiment_dir):
    # Figure 8
    apps = ["flux_msip", "flux_mscp"]
    data_sizes = ["105b", "105b"]
    sources = [2, 2]
    workers = [1, 4, 8, 16, 32, 64]

    xtick_labels = [str(w) for w in workers]

    #var = "all_throughput"
    var1 = "normalized_throughput"
    var2 = "avg_event_time_latency"
    for i in range(len(apps)):
        exp_local = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=True, is_buffered=False)
        exp_cori = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=False, is_buffered=False)

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_local.add_setup(sources[i], workers[j])
            exp_cori.add_setup(sources[i], workers[j])

        exp_local.process()
        exp_cori.process()

        #apps_var_raw_values = [
        #    exp_local.get_agg_results(var, method=AggregateMethod.RAW_LIST),
        #    exp_cori.get_agg_results(var, method=AggregateMethod.RAW_LIST)
        #]

        apps_tput_avg_values = [
            exp_local.get_agg_results(var1, method=AggregateMethod.RAW_VAL),
            exp_cori.get_agg_results(var1, method=AggregateMethod.RAW_VAL)
        ]

        apps_latency_avg_values = [
            exp_local.get_agg_results(var2, method=AggregateMethod.RAW_VAL),
            exp_cori.get_agg_results(var2, method=AggregateMethod.RAW_VAL)
        ]

        box_plot = BoxPlot(plot_filename="tput_%s_2_modes_live_w_1_64" % apps[i],
                           xlabel="Number of Workers",
                           ylabel="Throughput\n(tasks/s)",
                           legend_size=20, legend_loc="best")

        box_plot.plot(
            apps_tput_avg_values,
            xtick_labels,
            legends=["Local", "Remote"]
        )

        box_plot = BoxPlot(plot_filename="latency_%s_2_modes_live_w_1_64" % apps[i],
                           xlabel="Number of Workers",
                           ylabel="Latency (s)",
                           legend_size=20, legend_loc="best")

        box_plot.plot(
            apps_latency_avg_values,
            xtick_labels,
            legends=["Local", "Remote"],
        )


def tput_3_apps_cori_buffered_w_64_640(experiment_dir):
    # Figure 9 
    apps = ["als", "flux_msip", "flux_mscp"]
    data_sizes = ["10mb", "105b", "105b"]
    sources = [1, 2, 2]
    workers = [64, 128, 256, 512, 640]

    xtick_labels = [str(w) for w in workers]

    var = "normalized_throughput"
    std_var = "std_throughput"
    for i in range(len(apps)):
        if apps[i] == "als":
            exp_cori = Experiment(apps[i], data_sizes[i], experiment_dir,
            is_local=False, is_buffered=True)
        else:
            exp_cori = Experiment(apps[i], data_sizes[i], experiment_dir,
            is_local=False, is_buffered=True, scaling_style="strong_scaling")

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_cori.add_setup(sources[i], workers[j])

        exp_cori.process()

        ylim_top = None
        if apps[i] == "als":
            ylim_top = 10
        else:
            ylim_top = 20000
        bar_plot = BarPlot(plot_filename="tput_%s_cori_buffered_w_64_640" % apps[i],
                           xlabel="Number of Workers",
                           ylabel="Throughput\n(tasks/s)", ylim_top=ylim_top)

        bar_plot.plot(
            [exp_cori.get_agg_results(var)],
            xtick_labels,
            std_arrs=[exp_cori.get_agg_results(var, AggregateMethod.STD)])


def tput_1_app_cori_buffered_w_128_640_weak_scaling(experiment_dir):
    # Figure 10 A
    apps = ["flux_msip"]
    data_sizes = ["105b"]
    sources = [2, 4, 6, 8, 10]
    workers = [128, 256, 384, 512, 640]

    xtick_labels = [str(w) for w in workers]

    var = "normalized_throughput"
    for i in range(len(apps)):
        exp_cori = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=False, is_buffered=True, scaling_style="weak_scaling")

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_cori.add_setup(sources[j], workers[j])

        exp_cori.process()

        line_plot = LinePlot(plot_filename="tput_%s_cori_buffered_w_128_640_weak_scaling" % apps[i],
                           xlabel="Number of Workers",
                           ylabel="Throughput\n(tasks/s)",
                           ylim_bottom=0, ylim_top=9000)

        line_plot.plot(
            [exp_cori.get_agg_results(var)],
            xtick_labels,
            "--o")


def tput_1_app_cori_buffered_w_64_throttling(experiment_dir):
    # Figure 10 B
    apps = ["als"]
    data_sizes = ["10mb"]
    sources = [1]
    workers = [64]

    #TODO read job count files
    pass


def tput_1_app_cori_live_w_640_payload_2_10_mb(experiment_dir):
    # Figure 11
    apps = ["als"]
    data_sizes = ["2mb", "4mb", "6mb", "8mb", "10mb"]
    sources = [1]
    workers = [640]

    xtick_labels = data_sizes

    apps_var_avg_values = []
    apps_var_std_values = []
    #var = "all_throughput"
    var = "normalized_throughput"
    for i in range(len(data_sizes)):
        exp_cori = Experiment(apps[0], data_sizes[i], experiment_dir,
        is_local=False, is_buffered=False)

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_cori.add_setup(sources[j], workers[j])

        exp_cori.process()

        #res = exp_cori.get_agg_results(var, AggregateMethod.RAW_LIST)
        #apps_var_raw_values.append(res[0])

        apps_var_avg_values.append(exp_cori.get_agg_results(var, AggregateMethod.MEAN)[0])
        apps_var_std_values.append(exp_cori.get_agg_results(var, AggregateMethod.STD)[0])

    #print(len(apps_var_raw_values[0]))

    bar_plot = BarPlot(plot_filename="tput_%s_cori_live_w_640_payload_2_10_mb" % apps[0],
                       xlabel="Data-sizes (MB)",
                       ylabel="Throughput\n(tasks/s)",
                       ylim_top=10)

    bar_plot.plot(
        [apps_var_avg_values],
        xtick_labels,
        std_arrs=[apps_var_std_values]
    )


def latency_1_app_cori_live_w_640_payload_2_10_mb(experiment_dir):
    # Figure 12
    apps = ["als"]
    data_sizes = ["2mb", "4mb", "6mb", "8mb", "10mb"]
    sources = [1]
    workers = [640]

    xtick_labels = data_sizes

    apps_var_avg_values = []
    apps_var_std_values = []
    var = "avg_event_time_latency"
    for i in range(len(data_sizes)):
        exp_cori = Experiment(apps[0], data_sizes[i], experiment_dir,
        is_local=False, is_buffered=False)

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_cori.add_setup(sources[j], workers[j])

        exp_cori.process()

        #res = exp_cori.get_agg_results(var, AggregateMethod.RAW_LIST)
        #apps_var_raw_values.append(res[0])

        apps_var_avg_values.append(exp_cori.get_agg_results(var, AggregateMethod.MEAN)[0])
        apps_var_std_values.append(exp_cori.get_agg_results(var, AggregateMethod.STD)[0])

        bar_plot = BarPlot(plot_filename="latency_%s_cori_live_w_640_payload_2_10_mb" % apps[0],
                           xlabel="Data-sizes (MB)",
                           ylabel="Latency (s)",
                           ylim_bottom=0)

    print(apps_var_avg_values)
    print(apps_var_std_values)
    bar_plot.plot(
        [apps_var_avg_values],
        xtick_labels,
        std_arrs=[apps_var_std_values]
    )


def tput_2_apps_cori_live_w_64_pipeline_vs_non_pipeline(experiment_dir):
    # Figure 13
    apps = ["als", "flux_msip"]
    data_sizes = ["10mb", "105b"]
    sources = [1, 2]
    workers = [64]

    xtick_labels = ["ImageAnalysis", "MovingAverage"]

    var = "normalized_throughput"
    std_var = "std_throughput"
    pass


# example
def tput_1_app_cori_live_w_1_64(experiment_dir):
    # example
    apps = ["flux_msip"]
    data_sizes = ["105b"]
    sources = [2]
    workers = [1, 4, 8, 16, 32, 64]

    xtick_labels = [str(w) for w in workers]

    var = "normalized_throughput"
    std_var = "std_throughput"
    for i in range(len(apps)):
        exp_cori = Experiment(apps[i], data_sizes[i], experiment_dir,
        is_local=False, is_buffered=False)

        for j in range(len(workers)):
            # Adding Setup convention telling how many sources
            # and workers were running for that experiment
            exp_cori.add_setup(sources[i], workers[j])

        exp_cori.process()

        bar_plot = BarPlot(plot_filename="tput_%s_cori_buffered_w_64_640" % apps[i],
                           xlabel="Number of Workers",
                           ylabel="Throughput\n(tasks/s)")

        bar_plot.plot(
            [exp_cori.get_agg_results(var)],
            xtick_labels,
            legends=["ALS"],
            std_arrs=exp_cori.get_agg_results(std_var))


def main(args):
    experiment_dir = args.experiment_dir
    figure_num = args.figure_num

    #tput_1_app_cori_live_w_1_64(experiment_dir)

    if figure_num == 0:
        tput_redis_benchmark_bar_set_get(experiment_dir)
        tput_redis_benchmark_line_set(experiment_dir)
        tput_redis_benchmark_line_get(experiment_dir)
        tput_latency_3_apps_local_live_buffered_w_1(experiment_dir)
        #tput_3_apps_2_modes_buffered_w_1_64(experiment_dir)
        tput_2_apps_2_modes_live_w_1_64(experiment_dir)
        exit()
        tput_3_apps_cori_buffered_w_64_640(experiment_dir)
        tput_1_app_cori_buffered_w_128_640_weak_scaling(experiment_dir)
        tput_1_app_cori_buffered_w_64_throttling(experiment_dir)
        tput_1_app_cori_live_w_640_payload_2_10_mb(experiment_dir)
        latency_1_app_cori_live_w_640_payload_2_10_mb(experiment_dir)
    elif figure_num == 4:
        tput_redis_benchmark_bar_set_get(experiment_dir)
    elif figure_num == 5:
        tput_redis_benchmark_clients_line_set_get(experiment_dir)
    elif figure_num == 6:
        tput_latency_3_apps_local_live_buffered_w_1(experiment_dir)
    elif figure_num == 7:
        #tput_3_apps_2_modes_buffered_w_1_64(experiment_dir)
        pass
    elif figure_num == 8:
        tput_2_apps_2_modes_live_w_1_64(experiment_dir)
    elif figure_num == 9:
        tput_3_apps_cori_buffered_w_64_640(experiment_dir)
    elif figure_num == 10:
        tput_1_app_cori_buffered_w_128_640_weak_scaling(experiment_dir)
        tput_1_app_cori_buffered_w_64_throttling(experiment_dir)
    elif figure_num == 11:
        tput_1_app_cori_live_w_640_payload_2_10_mb(experiment_dir)
    elif figure_num == 12:
        latency_1_app_cori_live_w_640_payload_2_10_mb(experiment_dir)
    elif figure_num == 13:
        tput_2_apps_cori_live_w_64_pipeline_vs_non_pipeline(experiment_dir)
    elif figure_num < 4:
        raise ValueError("Figure %d cannot be generated" % figure_num)
    else:
        raise ValueError("Figure %d doesn't exist" % figure_num)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-e', '--experiment_dir', type=str, required=False,
        default=_settings.EXPERIMENT_DIR,
        help='Path to all experiments'
    )

    parser.add_argument(
        '-f', '--figure_num', type=int, required=False, default=0,
        help='Choose figure-num (from paper) to display. Default is 0 -- all figures'
    )

    args = parser.parse_args()

    main(args)
