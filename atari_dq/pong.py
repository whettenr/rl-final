import gym
import gym.spaces

DEFAULT_ENV_NAME = "PongNoFrameskip-v4"
test_env = gym.make(DEFAULT_ENV_NAME)
print(test_env.action_space.n)
print(test_env.unwrapped.get_action_meanings())
print(test_env.observation_space.shape)
