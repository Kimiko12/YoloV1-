import torch 
import torch.nn as nn 


# Backbone
architecture_config = [
    # Tuple: (kernek_size, number_of_filters, stride, padding)
    (7, 64, 2, 3),
    'MaxPooling',
    (3, 192, 1, 1),
    'MaxPooling',
    (1, 128, 1, 0),
    (3, 256, 1, 1),
    (1, 256, 1, 0),
    (3, 512, 1, 1),
    'MaxPooling',
    # List: number of tupels and then int that represent number of repeats
    [(1, 256, 1, 0), (3, 512 , 1, 1), 4],
    (1, 512, 1, 0),
    (3, 1024, 1, 1),
    'MaxPooling', 
    [(1, 512, 1, 0), (3, 1024, 1, 1), 2],
    (3, 1024, 1, 1),
    (3, 1024, 2, 1),
    (3, 1024, 1, 1),
    (3, 1024, 1, 1)
]


class CNNBlock(nn.Module):
    def __init__(self, input_channels, output_channels, **kwargs):
        super(CNNBlock, self).__init__()
        self.conv = nn.Conv2d(in_channels = input_channels, out_channels = output_channels, bias = False, **kwargs)
        self.batchnorm = nn.BatchNorm2d(output_channels)
        self.leakyrelu = nn.LeakyReLU(0.1)
    
    def forward(self, x):
        return self.leakyrelu(self.batchnorm(self.conv(x)))
    
class YoloV1(nn.Module):
    def __init__(self , in_channels = 3, **kwargs):
        super(YoloV1, self).__init__()
        self.architecture = architecture_config
        self.input_channels = in_channels
        self.darknet = self._create_conv_layers(self.architecture)
        self.fcs = self._crate_fcs(**kwargs)
        
    def forward(self, x):
        x = self.darknet(x)
        return self.fcs(torch.flatten(x, start_dim = 1))
    
    
    def _create_conv_layers(self, architecture): #DarkNet
        layers = []
        input_channels = self.input_channels
        for x in architecture:
            if type(x) == tuple:
                 layers += [CNNBlock(input_channels=input_channels, output_channels = x[1],
                                     kernel_size = x[0], stride = x[2], padding = x[3])]
                 
                 input_channels = x[1]
                 
            elif type(x) == str:
                layers += [nn.MaxPool2d(kernel_size=2, stride = 2)]
            elif type(x) == list:
                conv1 = x[0] # Tuple
                conv2= x[1] # tuple
                number_of_repeats = x[2] # int
                
                for _ in range(number_of_repeats):
                    layers += [CNNBlock(input_channels=input_channels, output_channels=conv1[1],
                                        kernel_size = conv1[0], stride = conv1[2], padding = conv1[3])]
                    layers += [CNNBlock(input_channels = conv1[1], output_channels = conv2[1],
                                        kernel_size = conv2[0], stride = conv2[2], padding = conv2[3])]
                    input_channels = conv2[1]
                
        return nn.Sequential(*layers)
    
        
    def _crate_fcs(self, split_size, num_boxes, num_classes):
        S, B, C = split_size, num_boxes, num_classes
        return nn.Sequential(
            nn.Flatten(),
            nn.Linear(1024 * S * S, 4096),
            nn.Dropout(0.0),
            nn.LeakyReLU(0.1),
            nn.Linear(4096, S * S * (C + B * 5)) # (S, S, 30), where S = C + B * 5
        )

def test(S = 7, B = 2, C = 20):
    model = YoloV1(split_size = S, num_boxes = B, num_classes = C)
    x = torch.randn((2, 3, 448, 448))
    print(model(x).shape)
    
test()