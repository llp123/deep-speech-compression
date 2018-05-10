#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun May  6 15:53:15 2018

@author: Samuele Garda
"""

import tensorflow as tf

def parse_tfrecord_example(proto):
  """
  Used to parse examples in tf.data.Dataset. 
  Each example is mapped in its feature representation and its labels (int encoded transcription of audio).
  
  :param:
    proto (tf.Tensor) : element stored in tf.data.TFRecordDataset
    
  :return:
    dense_audio (tf.Tensor) : audio
    dense_trans (tf.Tensor) : encoded transcription
  
  """
  
  features = {"audio": tf.VarLenFeature(tf.float32),
              "audio_shape": tf.FixedLenFeature((2,), tf.int64),
              "labels": tf.VarLenFeature(tf.int64)}
  
  parsed_features = tf.parse_single_example(proto, features)
  
  sparse_audio = parsed_features["audio"]
  shape = tf.cast(parsed_features["audio_shape"], tf.int32)
  dense_audio = tf.reshape(tf.sparse_to_dense(sparse_audio.indices,
                                              sparse_audio.dense_shape,
                                              sparse_audio.values),shape)
  
  sparse_trans = parsed_features["labels"]
  dense_trans = tf.sparse_to_dense(sparse_trans.indices,
                                   sparse_trans.dense_shape,
                                   sparse_trans.values)
  return dense_audio, tf.cast(dense_trans, tf.int32)



def model_input_func_tfr(tfrecord_path, split, shuffle, batch_size):
  """
  Create dataset instance from tfrecord file. It prefetches mini-batch. If is train split dataset is repeated.
  
  :param:
    tfrecord_path (str) : path to tfrecord file.
    split (str) : part of the dataset. Choiches = (`train`,`dev`,`test`)
    shuffle (int) : buffer size for shuffle operation
    batch_size (int) : size of mini-batches
    
  :return:
    minibatch (batch_features,batch_labels) : minibatch (features, labels)
  """
    
  dataset = tf.data.TFRecordDataset(tfrecord_path)
  
  dataset = dataset.map(parse_tfrecord_example)
  
  dataset = dataset.shuffle(buffer_size=shuffle)
  
  if split == 'train':
    
    dataset = dataset.repeat()
        
  dataset = dataset.padded_batch(batch_size, padded_shapes=(tf.TensorShape([None,None]),tf.TensorShape([None])))
  
  dataset = dataset.prefetch(batch_size)
  
  iterator = dataset.make_one_shot_iterator()
  
  features, labels = iterator.get_next()
    
  return features, labels


if __name__ == "__main__":
  
  next_element = model_input_func_tfr('./test/librispeech_tfrecords.dev', shuffle = 10,
                                   split = 'dev', batch_size = 5)
  
  with tf.Session() as sess:
    for i in range(2):
      try:
        batch_x,  batch_y = sess.run(next_element)
#        print(values)
        print([x.shape for x in batch_x])
        print('\n\n') 
      except tf.errors.OutOfRangeError:
        print("End of dataset")