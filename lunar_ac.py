import gym
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import time

# Configuration parameters for the whole setup
# seed = 1
# env.seed(seed)
# tf.random.set_seed(seed)
# np.random.seed(seed)
def run(gamma, num_hidden, lr, max_eps=1000000):
    # gamma = 0.99  # Discount factor for past rewards
    max_steps_per_episode = 10000
    env = gym.make("LunarLander-v2")  # Create the environment
    # env = gym.make("Pendulum-v1")  # Create the environment

    eps = np.finfo(np.float32).eps.item()  
    print("ACTION SPACE: ", env.action_space)
    # num_inputs = 3
    # num_actions = 1
    num_inputs = 8
    num_actions = 4
    # num_hidden = 12

    inputs = layers.Input(shape=(num_inputs,))
    common = layers.Dense(num_hidden, activation="relu")(inputs)
    action = layers.Dense(num_actions, activation="softmax")(common)
    # action = layers.Dense(num_actions, activation="sigmoid")(common)
    # action = layers.Dense(num_actions)(common)
    critic = layers.Dense(1)(common)

    model = keras.Model(inputs=inputs, outputs=[action, critic])

    optimizer = keras.optimizers.Adam(learning_rate=lr)
    huber_loss = keras.losses.Huber()
    action_probs_history = []
    critic_value_history = []
    rewards_history = []
    running_reward = []
    episode_count = 0

    # while True:  # Run until solved
    for i in range(max_eps):  # Run for x number os episodes
        state = env.reset()
        episode_reward = 0
        with tf.GradientTape() as tape:
            for timestep in range(1, max_steps_per_episode):
                # env.render(); #Adding this line would show the attempts
                # of the agent in a pop up window.

                state = tf.convert_to_tensor(state)
                state = tf.expand_dims(state, 0)

                # Predict action probabilities and estimated future rewards
                # from environment state
                action_probs, critic_value = model(state)
                critic_value_history.append(critic_value[0, 0])

                # Sample action from action probability distribution
                # print('action_probs')
                # print(np.squeeze(action_probs))
                action = np.random.choice(num_actions, p=np.squeeze(action_probs))
                # action = np.random.choice(num_actions, p=np.squeeze(action_probs))
                action_probs_history.append(tf.math.log(action_probs[0, action]))

                # Apply the sampled action in our environment
                state, reward, done, _ = env.step(action)
                rewards_history.append(reward)
                episode_reward += reward

                if done:
                    break

            # Update running reward to check condition for solving
            # running_reward = 0.05 * episode_reward + (1 - 0.05) * running_reward
            running_reward.append(episode_reward)

            # Calculate expected value from rewards
            # - At each timestep what was the total reward received after that timestep
            # - Rewards in the past are discounted by multiplying them with gamma
            # - These are the labels for our critic
            returns = []
            discounted_sum = 0
            for r in rewards_history[::-1]:
                discounted_sum = r + gamma * discounted_sum
                returns.insert(0, discounted_sum)

            # Normalize
            returns = np.array(returns)
            returns = (returns - np.mean(returns)) / (np.std(returns) + eps)
            returns = returns.tolist()

            # Calculating loss values to update our network
            history = zip(action_probs_history, critic_value_history, returns)
            actor_losses = []
            critic_losses = []
            for log_prob, value, ret in history:
                # At this point in history, the critic estimated that we would get a
                # total reward = `value` in the future. We took an action with log probability
                # of `log_prob` and ended up recieving a total reward = `ret`.
                # The actor must be updated so that it predicts an action that leads to
                # high rewards (compared to critic's estimate) with high probability.
                diff = ret - value
                actor_losses.append(-log_prob * diff)  # actor loss

                # The critic must be updated so that it predicts a better estimate of
                # the future rewards.
                critic_losses.append(
                    huber_loss(tf.expand_dims(value, 0), tf.expand_dims(ret, 0))
                )

            # Backpropagation
            loss_value = sum(actor_losses) + sum(critic_losses)
            grads = tape.gradient(loss_value, model.trainable_variables)
            optimizer.apply_gradients(zip(grads, model.trainable_variables))

            print(episode_reward)
            # Clear the loss and reward history
            action_probs_history.clear()
            critic_value_history.clear()
            rewards_history.clear()

        # Log details
        episode_count += 1
        if episode_count % 10 == 0:
            template = "avg reward: {:.2f} at episode {}"
            print(template.format(np.mean(np.array(running_reward)), episode_count))

        if np.mean(np.array(running_reward)) > 0:  # Condition to consider the task solved
            print("Solved at episode {}!".format(episode_count))
            return episode_count, running_reward, model
    return episode_count, running_reward, model


if __name__ == '__main__':
    hidden_n = [4, 16, 64, 128, 256]
    gammas = [0.1, 0.3, 0.5, 0.8, 0.99]
    lrs = [0.001, 0.01, 0.1]
    for hidden in hidden_n:
      for gamma in gammas:
        for lr in lrs:
          for i in range(5):
            start = time.time()
            count, reward, model = run(gamma=gamma, num_hidden=hidden, lr=lr, max_eps=10000)
            end = time.time()
            with open('time-acll-.txt', 'a') as f:
                f.write(str(hidden)+'|' + str(gamma)+'|' +str(lr)+'|'+ str(end - start) +'|' + str(count) + '|' + str(reward) + "\n")
                f.close()
            model.save('models/acll-' + str(hidden)+ '-' + str(gamma)+ '-' +str(lr)+ '-' + str(i))



