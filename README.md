# Listen to the Teacher!

Submission for Indivudual Research project, Summer Semester 2018, University of Potsdam. 

Exploring different teacher-student training technique to transfer knowledge of deep learnging Automatic Speech Recognition systems to smaller deployable student network.

In the project are explored three different training techniques:
- Distillation
- Quanitzed Distillation
- FitNets

All the models here implemented are fully based on **1D convolutional layers** .

## Install 

Download or clone the git repo https://github.com/sgarda/deep-speech-compression

## Input Data
In order to reproduce all the experiments free space storage shouldn't be a problem for you. All the training is done on the [LibriSpeech](http://www.openslr.org/12/) corpus and the unzipped folder is ~30GB.
To create the input data compatible with the [Tensorflow input pipeline](https://www.tensorflow.org/guide/datasets) it is necessary to create `tfrecord` file for each split in the corpus. 

All the audio files are processed with [`librosa`](https://librosa.github.io/librosa/) python library. It is possible to set the type of representation to be used for the audio with `--format`. 
The available option are :
- `raw` : store raw wave
- `power` : power spectrogram
- `mfccs` : mel-frequencies cepstral coefficient(s)

For power spectrograms and mfccs features the default values of the window size and the stride are 32ms and 10ms respectively. The values are set with the assumption that the corpus has a sampling rate of 16 kHz. If you wish to modify these values please edit the corresponding [source code](https://github.com/sgarda/deep-speech-compression/blob/master/utils/data2tfrecord.py#L330) .

    python3 -m utils.create_tfrecords.py --data <corpus folder> --out <folder save data> --split train
    
The split argument accepts a comma separeted list of sets. It is possible to specify a specific folder (e.g. "dev-clean") or merging alle the folders within a given split (e.g. "dev" merge in one file "dev-clean" and "dev-other"). 
Since this is an expensive operation the data is processed in parallel on multiple CPUs. You can set the amount of available processing units with `--cores`.

At the end of the process in the specified output folder will be created - besides the `tfrecord` files - a file containing the vocabulary lookup and the compressed file containing all the transcriptions with their ids. This can be usefull if you wish to process the various splits on multiple sessions. With the arguments `--cached-ids2trans` and `--cached-chars2ids` you can load the data already generated for skipping the vocabulary generation step.
As a final not the argument `--loss` allows you to specify with which loss the models is going to be trained, which affects the vocabulary. As of now the **only** available loss is Tensorflow's  implementation of CTC.


### Teacher Model
Once the all the necessaries input files are generated it is possible to train the Teacher network. In order to do so you just need to created a configuration.

    python model_main.py --mode train --conf ./configs/teacher.config
    
The configuration file has several section specifying the model architectures (e.g. `bn` for useing batch normalization) and paths to all the files that are needed for training/evaluating the model. Take a look at the `config` folder for several examples.

A special care needs to be taken for the following:
- input_channels : this specify the number of channels of the training examples. For instance with mfccs with 13 coefficients this results in 39 (first order and second order derivatives are used)
- conv_type : type of convolution to be used. If not `conv` the model will use `gated convolution` which will significantly increase the number of parameters of your model
- [TEACHER] or [STUDENT] : under this section you can design the model. All the layers are specified with 4 lists containing for each layer : number of filters, kernel width , stride and dropout probability. All these lists **must** have equal length! 

### Create Guidance

Once the teacher model is trained it is possible to save in a separete `tfrecord` file the "guidance" for each example in the training set, to be then used to train the student network. It is possible to save the teacher model logits as in [(1)](#references) :
    
    python3 -m utils.guide2tfrecord --p <out folder> --t <path to saved model dir> -g logits --conf ./configs/all_models/wav2letter_v1.config
    
If instead you wish to train a FitNet network as in [(3)](#references) you can pass `-g hints` and specify which layer of the teacher model is used for genereating the hints : `--up-to`.


## Train Students

Now that the guidance files have been generated, training the student networks is as simple as:

    python model_main.py --mode train --conf ./configs/student.config
    
where in the configuration file the `model_type = student`
    
Each type of student training has its own specifics that need to be set.

### Distilled Student

To train a student network with the distillation loss as in [(1)](#references) you need to specify additionally:

- teacher_logits : path to the `tfrecord` file storing the teacher logits for each training example
- temperature : the temperature used for distilling the logits
- alpha : the weighting factor for the averaged loss (CTC + cross entropy between teacher and students logits)

### Quantized Distilled Student

The technique introduced by [(2)](#references) allows to introduce quantization in the distillation process. In addition to the parameters of the distillation, you need to set:
- num_bits : number of bits for representing the quantized weights
- bucket_size : for better result in scaling (applied before quantization) the weights are firstly bucketed to this size 
- stochastic : use stochastic rounding in quantization

### FitNet

To train the student network as presented in [(3)](#references) it is necessary to go through two stages. In the first stage the student netwok up to the specified layer is trained to match (MSE) the hidden representation of the teacher for each training examples.
After this step is completed the whole student network is trained with the distillation loss as in [(1)](#references).
Thus you need to specify:
- teacher_hints : path to the hidden representations of the teacher model
- stage : 1 for MSE or 2 for distillation loss
- guided : all student layers <= this number are trained in the first stage

## Post-mortem quantization

If you wisch to directly quantize a model you have trained with the quantization function by [(2)](#references) you can use:
    
    python3 -m utils.pm_quantization --orig <path to model to be quantized> --pm <out folder> 
    
The quantization parameters are the same as for training a quantized student. Once the process is completed a separate folder containing the quantized model will be created. You can the use this folder to restore the model as deploy it.

## Language Model



## References

1) Hinton, Geoffrey, Oriol Vinyals, and Jeff Dean. "Distilling the knowledge in a neural network." arXiv preprint arXiv:1503.02531 (2015).

2) Polino, Antonio, Razvan Pascanu, and Dan Alistarh. "Model compression via distillation and quantization." arXiv preprint arXiv:1802.05668 (2018).

3) Romero, Adriana, et al. "Fitnets: Hints for thin deep nets." arXiv preprint arXiv:1412.6550 (2014).


    


