import argparse
import math
import os

import numpy as np

import tensorflow as tf


def make_graph(features, labels, num_hidden=8):
  hidden_weights = tf.Variable(tf.truncated_normal(
      [2, num_hidden],
      stddev=1/math.sqrt(2)
  ))
  tf.summary.image('hidden_weights', tf.expand_dims([hidden_weights], -1))

  # Shape [4, num_hidden]
  hidden_activations = tf.nn.relu(tf.matmul(features, hidden_weights))
  tf.summary.image('hidden_activations', tf.expand_dims([hidden_activations], -1))

  output_weights = tf.Variable(tf.truncated_normal(
      [num_hidden, 2],
      stddev=1/math.sqrt(num_hidden)
  ))
  tf.summary.image('output_weights', tf.expand_dims([output_weights], -1))

  # Shape [4, 2]
  logits = tf.matmul(hidden_activations, output_weights)
  tf.summary.image('logits', tf.expand_dims([logits], -1))

  cross_entropy = tf.nn.sparse_softmax_cross_entropy_with_logits(logits, labels)
  loss = tf.reduce_mean(cross_entropy)
  tf.summary.scalar('loss', loss)

  # Shape [4]
  predictions = tf.argmax(tf.nn.softmax(logits), 1)
  accuracy, update_acc = tf.contrib.metrics.streaming_accuracy(predictions, labels)
  tf.summary.scalar('accuracy', accuracy)

  gs = tf.Variable(0, trainable=False)
  optimizer = tf.train.GradientDescentOptimizer(0.2)

  grads_and_vars = optimizer.compute_gradients(loss)

  gradients = zip(grads_and_vars)[0]
  tf.summary.histogram('gradients', gradients)

  train_op = optimizer.apply_gradients(grads_and_vars, global_step=gs)

  return train_op, loss, gs, update_acc


def main(output_dir, checkpoint_every, num_steps):
  graph = tf.Graph()

  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  with graph.as_default():
    features = tf.placeholder(tf.float32, shape=[4, 2])
    labels = tf.placeholder(tf.int32, shape=[4])

    train_op, loss, gs, update_acc = make_graph(features, labels)
    init = tf.global_variables_initializer()
    init_local = tf.local_variables_initializer()
    summary_op = tf.summary.merge_all()


  writer = tf.summary.FileWriter(output_dir, graph=graph, flush_secs=1)

  with tf.Session(graph=graph) as sess:
    init.run()
    init_local.run()
    step = 0
    xy = np.array([
        [True, False],
        [True, True],
        [False, False],
        [False, True]
    ], dtype=np.float)
    y_ = np.array([True, False, False, True], dtype=np.int32)
    while step < num_steps:

      _, _, step, loss_value, summaries = sess.run(
          [train_op, update_acc, gs, loss, summary_op],
          feed_dict={features: xy, labels: y_}
      )
      if step % checkpoint_every == 0:
         writer.add_summary(summaries, global_step=step)


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--num-steps', type=int, default=5000)
  parser.add_argument(
      '--output-dir',
      type=os.path.abspath,
      default=os.path.abspath('output')
  )
  parser.add_argument('--checkpoint-every', type=int, default=1)
  args = parser.parse_args()
  main(args.output_dir, args.checkpoint_every, args.num_steps)