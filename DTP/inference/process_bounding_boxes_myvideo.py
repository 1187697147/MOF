"""
This file processes bounding boxes from the BDD-10K dataset and stores them in
pickle format. The code is similar to processes_bounding_boxes_jaad.py but is
more efficient and adapted for BDD.

The processed boxes contain the following important fields:

Labeled:            Is this frame labeled? The pedestrian must have been tracked
                    for MIN_LENGTH_PAST previous frames and MIN_LENGTH_FUTURE
                    future frames.
Past_x, Past_y:     Past x and y coordinates of the bounding box centroid for
                    the previous MIN_LENGTH_PAST-1 frames and current frame
Future_x, Future_y: Future x and y coordinates of the bounding box centroid for
                    the future MIN_LENGTH_FUTURE frames
"""
"""
    处理YoLo、Fatser-RCNN的检测框，检测文件组织形式与MOF差不多，仅仅保存满足跟踪的数据。
    增加了一些新的条目，每一帧都有一个存放前10帧位置的数组。
"""

import pandas as pd
import os
import cv2
from math import floor
import numpy as np
import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--detector',
                    '-d',
                    help="Use detections from 'yolo' or 'faster-rcnn'",
                    type=str,
                    default='yolo')
args = parser.parse_args()

# 读取跟踪结果csv
if args.detector == 'yolo':
    # TRACK_PATH = '../../DeepSort_YOLOv4/clip_data/myvideo_yolo_detection.csv'
    TRACK_PATH = '../../DeepSort_YOLOv4/myvideo_yolo_detection.csv'
else:
    TRACK_PATH = '../data/bdd_10k_detections_faster-rcnn.csv'

SAVE_PATH = './data_inference/'

# 设置过去以及预测帧数
MIN_LENGTH_PAST = 30
MIN_LENGTH_FUTURE = 0
MIN_DETECTION_LENGTH = MIN_LENGTH_PAST + MIN_LENGTH_FUTURE
boxes = pd.read_csv(TRACK_PATH)

boxes['Requires_features'] = 0
boxes['Labeled'] = 0
# 格式：top left (x,y), bottom right (x,y)
boxes['Mid_x'] = (boxes['bb1'] + boxes['bb3']) / 2
boxes['Mid_y'] = (boxes['bb2'] + boxes['bb4']) / 2
boxes['Height'] = boxes['bb4'] - boxes['bb2']
boxes['Width'] = boxes['bb3'] - boxes['bb1']

boxes['Past_x'] = 0
boxes['Past_y'] = 0
boxes['Past_x'] = boxes['Past_x'].astype(object)
boxes['Past_y'] = boxes['Past_y'].astype(object)
print('原始数据: ',boxes.shape)

# 去除小目标
# boxes = boxes[boxes['Height'] > 50]
boxes = boxes.sort_values(by=['filename', 'track', 'frame_num'])
boxes = boxes.reset_index()
del boxes['index']


###  detection_length从0开始
boxes['Labeled'] = np.where(
    boxes['detection_length'] >= MIN_DETECTION_LENGTH - 1, 1,
    0) 
boxes['Labeled'] = boxes['Labeled'].shift(-MIN_LENGTH_FUTURE)

# 输出可跟踪的items
features = boxes[boxes['Labeled'] == 1]
print("label = 1: ", features.shape)


print('Storing centroids. This make take a few minutes.')
# Store MIN_LENGTH_PAST and future MIN_LENGTH_FUTURE bounding box centroids
past_x_names = []
for past in range(MIN_LENGTH_PAST, 0, -1):
    boxes['prev_x' + str(past)] = boxes['Mid_x'].shift(past)
    past_x_names.append('prev_x' + str(past))
past_y_names = []
for past in range(MIN_LENGTH_PAST, 0, -1):
    boxes['prev_y' + str(past)] = boxes['Mid_y'].shift(past)
    past_y_names.append('prev_y' + str(past))

boxes['Past_x'] = boxes[past_x_names].values.tolist()
boxes['Past_y'] = boxes[past_y_names].values.tolist()
boxes = boxes.dropna(subset=['filename'], axis=0)

if args.detector == 'yolo':
    print('ok yolo')
    boxes.to_pickle(SAVE_PATH + 'myvideo_location_features_yolo.pkl')
else:
    print('ok rcnn')
    boxes.to_pickle(SAVE_PATH + 'bdd_10k_location_features_faster-rcnn.pkl')

print('Done.')
