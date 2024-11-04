package deployment.terraform;

import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.ec2.Ec2Client;
import software.amazon.awssdk.services.ec2.model.*;
import software.amazon.awssdk.services.iam.IamClient;
import software.amazon.awssdk.services.iam.model.CreateRoleRequest;
import software.amazon.awssdk.services.iam.model.CreateRoleResponse;
import software.amazon.awssdk.services.iam.model.AttachRolePolicyRequest;
import software.amazon.awssdk.services.iam.model.AttachRolePolicyResponse;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.*;
import software.amazon.awssdk.services.lambda.LambdaClient;
import software.amazon.awssdk.services.lambda.model.*;

import java.util.HashMap;
import java.util.Map;

public class AWSProvisioning {

    private static final String BUCKET_NAME = "terraform-state-bucket";
    private static final String ROLE_NAME = "terraform-lambda-execution-role";
    private static final String FUNCTION_NAME = "terraform-lambda-function";
    private static final String INSTANCE_TAG = "TerraformEC2Instance";

    public static void main(String[] args) {
        AwsBasicCredentials awsCreds = AwsBasicCredentials.create("accessKeyId", "secretAccessKey");

        // Create S3 bucket for Terraform state
        createS3Bucket(awsCreds);

        // Create IAM Role for Lambda function
        String roleArn = createIamRole(awsCreds);

        // Deploy Lambda function
        deployLambdaFunction(awsCreds, roleArn);

        // Launch EC2 instance
        launchEc2Instance(awsCreds);
    }

    private static void createS3Bucket(AwsBasicCredentials awsCreds) {
        S3Client s3Client = S3Client.builder()
                .region(Region.US_EAST_1)
                .credentialsProvider(StaticCredentialsProvider.create(awsCreds))
                .build();

        CreateBucketRequest createBucketRequest = CreateBucketRequest.builder()
                .bucket(BUCKET_NAME)
                .build();

        try {
            s3Client.createBucket(createBucketRequest);
            System.out.println("S3 Bucket created: " + BUCKET_NAME);
        } catch (S3Exception e) {
            System.err.println(e.awsErrorDetails().errorMessage());
        }
    }

    private static String createIamRole(AwsBasicCredentials awsCreds) {
        IamClient iamClient = IamClient.builder()
                .region(Region.US_EAST_1)
                .credentialsProvider(StaticCredentialsProvider.create(awsCreds))
                .build();

        String assumeRolePolicyDocument = "{\n" +
                "  \"Version\": \"2012-10-17\",\n" +
                "  \"Statement\": [\n" +
                "    {\n" +
                "      \"Effect\": \"Allow\",\n" +
                "      \"Principal\": {\n" +
                "        \"Service\": \"lambda.amazonaws.com\"\n" +
                "      },\n" +
                "      \"Action\": \"sts:AssumeRole\"\n" +
                "    }\n" +
                "  ]\n" +
                "}";

        CreateRoleRequest createRoleRequest = CreateRoleRequest.builder()
                .roleName(ROLE_NAME)
                .assumeRolePolicyDocument(assumeRolePolicyDocument)
                .build();

        CreateRoleResponse createRoleResponse = iamClient.createRole(createRoleRequest);

        AttachRolePolicyRequest attachRolePolicyRequest = AttachRolePolicyRequest.builder()
                .roleName(ROLE_NAME)
                .policyArn("arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole")
                .build();

        AttachRolePolicyResponse attachRolePolicyResponse = iamClient.attachRolePolicy(attachRolePolicyRequest);
        System.out.println("IAM Role created: " + createRoleResponse.role().roleName());

        return createRoleResponse.role().arn();
    }

    private static void deployLambdaFunction(AwsBasicCredentials awsCreds, String roleArn) {
        LambdaClient lambdaClient = LambdaClient.builder()
                .region(Region.US_EAST_1)
                .credentialsProvider(StaticCredentialsProvider.create(awsCreds))
                .build();

        Map<String, String> environmentVariables = new HashMap<>();
        environmentVariables.put("VAR1", "value1");

        FunctionCode functionCode = FunctionCode.builder()
                .s3Bucket(BUCKET_NAME)
                .s3Key("lambda-deployment.zip")
                .build();

        CreateFunctionRequest createFunctionRequest = CreateFunctionRequest.builder()
                .functionName(FUNCTION_NAME)
                .runtime(Runtime.JAVA11)
                .role(roleArn)
                .handler("com.website.lambda.LambdaHandler::handleRequest")
                .code(functionCode)
                .environment(Environment.builder().variables(environmentVariables).build())
                .build();

        CreateFunctionResponse createFunctionResponse = lambdaClient.createFunction(createFunctionRequest);
        System.out.println("Lambda Function created: " + createFunctionResponse.functionName());
    }

    private static void launchEc2Instance(AwsBasicCredentials awsCreds) {
        Ec2Client ec2Client = Ec2Client.builder()
                .region(Region.US_EAST_1)
                .credentialsProvider(StaticCredentialsProvider.create(awsCreds))
                .build();

        RunInstancesRequest runInstancesRequest = RunInstancesRequest.builder()
                .instanceType(InstanceType.T2_MICRO)
                .imageId("ami-0abcdef1234567890")
                .maxCount(1)
                .minCount(1)
                .keyName("key-pair")
                .securityGroupIds("sg-0abc123def456gh78")
                .subnetId("subnet-0abc123def456gh78")
                .tagSpecifications(TagSpecification.builder()
                        .resourceType(ResourceType.INSTANCE)
                        .tags(Tag.builder().key("Name").value(INSTANCE_TAG).build())
                        .build())
                .build();

        RunInstancesResponse runInstancesResponse = ec2Client.runInstances(runInstancesRequest);

        String instanceId = runInstancesResponse.instances().get(0).instanceId();
        System.out.println("EC2 Instance created with ID: " + instanceId);
    }
}