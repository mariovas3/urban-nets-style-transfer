import numpy as np
import matplotlib.pyplot as plt
import pygame
from math import sqrt
import time
import torch
import pickle
import networkx as nx
from pathlib import Path

TESTS_DIR_PATH = Path(__file__).absolute().parent.parent / 'tests'
print(TESTS_DIR_PATH)


def see_one_episode(env, agent, seed, save_to):
    obs, info = env.reset(seed=seed)
    done = False
    step = 0
    obs_list = [obs]
    action_list = []
    while not done:
        time.sleep(1 / 60)  # slow down rendering, otherwise 125 fps;
        obs = torch.tensor(obs, dtype=torch.float32)
        action = agent.sample_deterministic(obs).numpy()
        action_list.append(action)
        obs, reward, terminated, truncated, info = env.step(action)
        obs_list.append(obs)
        done = terminated or truncated
        step += 1
        if terminated:
            print(f"simulation died step: {step}")
    # save episode;
    with open(save_to, 'wb') as f:
        pickle.dump(obs_list, f)
        pickle.dump(action_list, f)
    env.close()
    pygame.display.quit()


def vis_graph_building(edge_index, save_to):
    edges = []
    unique_edges = set()
    for first, second in zip(*edge_index):
        if first > second:
            first, second = second, first
        if (first, second) in unique_edges:
            continue
        edges.append((first, second))
        unique_edges.add((first, second))
        
    G = nx.Graph()
    fig = plt.figure(figsize=(12, 8))

    steps = len(edges)
    rows = int(sqrt(steps))
    cols = int(steps / rows) + (1 if steps % rows else 0)
    for i in range(steps):
        plt.subplot(rows, cols, i+1)
        G.add_node(edges[i][0])
        G.add_node(edges[i][1])
        G.add_edge(*edges[i])
        nx.draw_networkx(G)
    fig.tight_layout()
    file_name = save_to / f'last_episode_{len(edges)}_edges.png'
    plt.savefig(file_name)
    plt.close()


def save_metric_plots(metric_names, metrics, path, seed):
    file_name = f"metric-plots-seed-{seed}.png"
    file_name = path / file_name
    rows = int(sqrt(len(metrics)))
    cols = int(len(metrics) / rows) + (1 if len(metrics) % rows else 0)
    fig = plt.figure(figsize=(12, 8))
    for i, (metric_name, metric) in enumerate(sorted(zip(metric_names, metrics), key=lambda x: x[0])):
        plt.subplot(rows, cols, i + 1)
        ax = plt.gca()
        ax.plot(metric)
        ylow, yhigh = np.min(metric), np.max(metric)
        yoffset = max((yhigh - ylow) / 10, .1)
        xlow, xhigh = 0, len(metric) + 5
        ax.set_ylim(ylow, yhigh)
        ax.set_ylabel(metric_name)
        ax.set_yticks(np.arange(ylow-1.5 * yoffset, 
                                yhigh+1.5 * yoffset, 
                                yoffset))
        ax.set_xticks(np.arange(xlow, xhigh, (xhigh - xlow) / 10).round())
        ax.set_xticklabels(ax.get_xticks(), rotation=90)
    fig.tight_layout()
    plt.savefig(file_name)
    plt.close()


def visualise_episode(env, agent, seed, T=None):
    """
    Assumes env has "human" in env.metadata["render_modes"].
    """
    obs, info = env.reset(seed=seed)
    done = False
    t = 0
    pred = t < T if T else True
    while not done and pred:
        action = agent.sample_action(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        if T:
            t += 1
            pred = t < T
        done = terminated or truncated
    pygame.display.quit()


def get_moving_avgs(returns_over_episodes, num_steps):
    """
    Return len(returns_over_episodes) - num_steps + 1 moving
    averages over num_steps steps.
    """
    if num_steps > len(returns_over_episodes):
        raise ValueError(
            "num_steps should be less than"
            " or equal to length of returns_over_episodes"
        )
    return (
        np.correlate(returns_over_episodes, np.ones(num_steps), mode="valid")
        / num_steps
    )


def ci_plot(ax, data: np.ndarray, **kwargs):
    """
    Plot mean +- std intervals along the rows of data.
    """
    x = np.arange(data.shape[-1])
    avg = np.mean(data, 0)
    sd = np.std(data, 0)
    ax.fill_between(x, avg - sd, avg + sd, alpha=0.2, **kwargs)
    ax.plot(x, avg, **kwargs)
