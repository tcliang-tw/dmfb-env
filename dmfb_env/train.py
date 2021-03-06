#!/usr/bin/python

import os
import time

import matplotlib
import matplotlib.pyplot as plt
import tensorflow as tf

from utils import OldRouter
from my_net import MyCnnPolicy
from envs.dmfb import*

from stable_baselines.common import make_vec_env
from stable_baselines.common.vec_env import DummyVecEnv
from stable_baselines.common.policies import MlpPolicy, CnnPolicy, MlpLstmPolicy
from stable_baselines.common.evaluation import evaluate_policy
from stable_baselines import PPO2

def legacyReward(env, b_path = False):
    """ Return the reward of a game if a legacy
        method is used
    """
    router = OldRouter(env)
    return router.getReward(b_path)

def EvaluatePolicy(model, env,
        n_eval_episodes = 100, b_path = False):
    episode_rewards = []
    legacy_rewards = []
    n_steps = 0
    for i in range(n_eval_episodes):
        obs = env.reset()
        done, state = False, None
        episode_reward = 0.0
        this_loop_steps = 0
        while not done:
            action, state = model.predict(obs)
            obs, reward, done, _info = env.step(action)
            reward = reward[0]
            done = done[0]
            episode_reward += reward
            n_steps += 1
            this_loop_steps += 1
            legacy_r = legacyReward(env.envs[0], b_path)
        if b_path:
            episode_rewards.append(this_loop_steps)
        else:
            episode_rewards.append(episode_reward)
        legacy_rewards.append(legacy_r)
    mean_reward = np.mean(episode_rewards)
    mean_legacy = np.mean(legacy_rewards)
    return mean_reward, n_steps, mean_legacy

def runAnExperiment(
        env,
        model = None,
        num_iterations = 50,
        num_steps = 20000,
        policy_steps = 128,
        b_path = False):
    if model is None:
        model = PPO2(MyCnnPolicy, env, n_steps = policy_steps)
    agent_rewards = []
    old_rewards = []
    episodes = []
    for i in range(num_iterations + 1):
        model.learn(total_timesteps = num_steps)
        mean_reward, n_steps, legacy_reward = EvaluatePolicy(model,
                model.get_env(), n_eval_episodes = 50, b_path = b_path)
        agent_rewards.append(mean_reward)
        old_rewards.append(legacy_reward)
        episodes.append(i)
    agent_rewards = agent_rewards[-num_iterations:]
    old_rewards = old_rewards[-num_iterations:]
    episodes = episodes[:num_iterations]
    return agent_rewards, old_rewards, episodes

def showIsGPU():
    if tf.test.is_gpu_available():
        print("### Training on GPUs... ###")
    else:
        print("### Training on CPUs... ###")

def plotAgentPerformance(a_rewards, o_rewards, size, env_info, b_path = False):
    a_rewards = np.array(a_rewards)
    o_rewards = np.array(o_rewards)
    a_line = np.average(a_rewards, axis = 0)
    o_line = np.average(o_rewards, axis = 0)
    a_max = np.max(a_rewards, axis = 0)
    a_min = np.min(a_rewards, axis = 0)
    o_max = np.max(o_rewards, axis = 0)
    o_min = np.min(o_rewards, axis = 0)
    episodes = list(range(len(a_max)))
    with plt.style.context('ggplot'):
        plt.rcParams.update({'font.size': 20})
        plt.figure()
        plt.fill_between(episodes, a_max, a_min, facecolor = 'red', alpha = 0.3)
        plt.fill_between(episodes, o_max, o_min, facecolor = 'blue',
                alpha = 0.3)
        plt.plot(episodes, a_line, 'r-', label = 'Agent')
        plt.plot(episodes, o_line, 'b-', label = 'Baseline')
        if b_path:
            leg = plt.legend(loc = 'upper left', shadow = True, fancybox = True)
        else:
            leg = plt.legend(loc = 'lower right', shadow = True,
                    fancybox = True)
        leg.get_frame().set_alpha(0.5)
        plt.title("DMFB " + size)
        plt.xlabel('Training Epochs')
        if b_path:
            plt.ylabel('Number of Cycles')
        else:
            plt.ylabel('Score')
        plt.tight_layout()
        plt.savefig('log/' + size + env_info + '.png')

def expSeveralRuns(args, n_e, n_s, n_repeat):
    size = str(args['w']) + 'x' + str(args['l'])
    env_info = '_m' + str(args['n_modules'])
    env = make_vec_env(DMFBEnv, n_envs = n_e, env_kwargs = args)
    showIsGPU()
    a_rewards = []
    o_rewards = []
    for i in range(n_repeat):
        a_r, o_r, episodes = runAnExperiment(env, num_iterations = 50,
                num_steps = 20000, policy_steps = n_s)
        a_rewards.append(a_r)
        o_rewards.append(o_r)
    plotAgentPerformance(a_rewards, o_rewards, size, env_info)

if __name__ == '__main__':
    sizes = [15]
    for s in sizes:
        args = {'w': s, 'l': s,
                'n_modules': 0,
                'b_degrade': True,
                'per_degrade': 0.1}
        expSeveralRuns(args, n_e = 1, n_s = 64, n_repeat = 3)
    print('### Finished train.py successfully ###')
