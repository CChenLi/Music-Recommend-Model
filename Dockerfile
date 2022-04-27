FROM public.ecr.aws/lambda/python:3.8

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}
COPY id_map.csv ${LAMBDA_TASK_ROOT}
COPY id_map.json ${LAMBDA_TASK_ROOT}
COPY GCN87.pt ${LAMBDA_TASK_ROOT}
COPY user_like_graph.json ${LAMBDA_TASK_ROOT}
COPY user_like.json ${LAMBDA_TASK_ROOT}


RUN pip3 install --target "${LAMBDA_TASK_ROOT}" --upgrade pip 
RUN pip3 install --target "${LAMBDA_TASK_ROOT}" numpy 
RUN pip3 install --target "${LAMBDA_TASK_ROOT}" pandas
RUN pip3 install --target "${LAMBDA_TASK_ROOT}" torch-1.11.0-cp310-cp310-manylinux1_x86_64.whl 
RUN pip3 install --target "${LAMBDA_TASK_ROOT}" torch-scatter -f https://data.pyg.org/whl/torch-1.11.0+cpu.html 
RUN pip3 install --target "${LAMBDA_TASK_ROOT}" torch-sparse -f https://data.pyg.org/whl/torch-1.11.0+cpu.html 
RUN pip3 install --target "${LAMBDA_TASK_ROOT}" torch-geometric 

CMD [ "app.handler" ]

# login
# aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 682475076944.dkr.ecr.us-east-1.amazonaws.com/cchenli