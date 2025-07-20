# 📄 Knowflow Infra Provisioning via AWS Console

## **1️⃣ VPC Setup**

- Go to **VPC Console** → **Your VPCs** → **Create VPC**:

  - Name: `KnowflowVPC`
  - IPv4 CIDR block: `10.0.0.0/16`
  - Tenancy: Default

### Create Subnets:

- Go to **Subnets** → **Create subnet**:

  - **Subnet 1**:

    - Name: `Public`
    - Subnet Type: Public
    - CIDR block: `10.0.0.0/24`
    - Availability Zone: Choose one

  - **Subnet 2**:

    - Name: `PrivateECS`
    - Subnet Type: Private (with NAT)
    - CIDR block: `10.0.1.0/24`

  - **Subnet 3**:

    - Name: `PrivateDB`
    - Subnet Type: Private (with NAT)
    - CIDR block: `10.0.2.0/24`

> Ensure subnets are associated with appropriate **Route Tables** and **NAT Gateway** for private subnets.

---

### **1️⃣ Create an Internet Gateway (IGW) for Public Subnets**

1. Go to **VPC Console** → **Internet Gateways**.
2. Click **Create internet gateway**:

   - Name: `Knowflow-IGW`.

3. Attach the IGW to your **KnowflowVPC**.

---

### **2️⃣ Create a NAT Gateway for Private Subnets**

1. Go to **VPC Console** → **NAT Gateways**.
2. Click **Create NAT gateway**:

   - Subnet: Choose your **Public Subnet**.
   - Elastic IP: Allocate a new Elastic IP.
   - Name: `Knowflow-NATGW`.

This NAT Gateway enables internet access for private subnets without exposing them directly.

---

### **3️⃣ Create Route Tables**

#### A. **Public Route Table** (For Public Subnet)

1. Go to **Route Tables** → **Create Route Table**:

   - Name: `Public-RT`.
   - VPC: Select `KnowflowVPC`.

2. After creation:

   - Select `Public-RT`.
   - Go to **Routes** tab → **Edit Routes**:

     - Add route:

       - Destination: `0.0.0.0/0`
       - Target: Your **Internet Gateway (IGW)**

3. Go to **Subnet Associations** → **Edit subnet associations**:

   - Select your **Public Subnet** (`Public`).

---

#### B. **Private Route Table** (For PrivateECS & PrivateDB)

1. Go to **Route Tables** → **Create Route Table**:

   - Name: `Private-RT`.
   - VPC: Select `KnowflowVPC`.

2. After creation:

   - Select `Private-RT`.
   - Go to **Routes** tab → **Edit Routes**:

     - Add route:

       - Destination: `0.0.0.0/0`
       - Target: Your **NAT Gateway**.

3. Go to **Subnet Associations** → **Edit subnet associations**:

   - Select both:

     - **PrivateECS Subnet**.
     - **PrivateDB Subnet**.

## **2️⃣ Security Groups**

### **ALB-SG**

- In **EC2 Console** → **Security Groups** → **Create security group**:

  - Name: `ALB-SG`
  - VPC: `KnowflowVPC`
  - Inbound Rules:

    - Allow TCP 80 (HTTP) from 0.0.0.0/0
    - Allow TCP 443 (HTTPS) from 0.0.0.0/0

### **ECS-SG**

- Name: `ECS-SG`
- VPC: `KnowflowVPC`
- No inbound rules needed (default outbound will suffice).

### **RDS-SG**

- Name: `RDS-SG`
- VPC: `KnowflowVPC`
- Inbound Rules:

  - Allow TCP 5432 (PostgreSQL) from `ECS-SG` (select the security group itself as source).

---

## **3️⃣ Secrets Manager**

- Go to **Secrets Manager** → **Store a new secret**:

  - Secret Name: `knowflow-app-secrets`
  - Secret Type: Other type of secret / Plaintext
  - Add key-value pairs as needed (like `SECRET_KEY`, `DATABASE_URL`, etc.)

---

## **4️⃣ ECR Repositories**

- Go to **ECR Console**:

  - Create Repository → Name: `FastAPIRepo`
  - Create Repository → Name: `Neo4jRepo`

Push your Docker images manually or via CI/CD.

---

## **5️⃣ IAM Role for ECS Tasks**

- Go to **IAM Console** → **Roles** → **Create Role**:

  - Trusted Entity: AWS service → ECS Task
  - Attach Policies:

    - SecretsManagerReadWrite (or custom policy scoped to your secret)
    - S3 permissions as per your project (`s3:PutObject`, `s3:GetObject`, etc.)

  - Role Name: `EcsTaskRole`

---

## **6️⃣ ECS Cluster**

- Go to **ECS Console** → **Clusters** → **Create Cluster**:

  - Cluster name: `KnowflowCluster`
  - VPC: Select `KnowflowVPC`

---

## **7️⃣ RDS PostgreSQL**

- Go to **RDS Console** → **Databases** → **Create database**:

  - Engine: PostgreSQL (version 15.3)
  - Template: Free tier or Production
  - Credentials:

    - Username: `postgres`
    - Password: Auto-generated or custom

  - Instance class: `db.t3.small` or similar
  - Storage: 20GB
  - Connectivity:

    - VPC: `KnowflowVPC`
    - Subnet group: Create a new one with `PrivateDB` subnets
    - Security Group: Attach `RDS-SG`
    - Public access: No

---

## **8️⃣ ECS Services**

### **A. FastAPI Service (ALB Fargate)**

- Go to **ECS Console** → **Clusters** → `KnowflowCluster`
- Create Service:

  - Launch Type: Fargate
  - Task Definition: Create a new one:

    - Container:

      - Image: From `FastAPIRepo`
      - Port Mapping: 8000
      - Environment variables: Add as required (`ENVIRONMENT=production`)
      - Task Role: Attach `EcsTaskRole`

    - Memory: 1024 MiB
    - CPU: 512 units

  - Service:

    - Desired Count: 1

  - Networking:

    - Subnets: `PrivateECS`
    - Security Group: `ECS-SG`
    - Load Balancer:

      - Create new ALB
      - Attach `ALB-SG`
      - Listener: Port 80
      - Target group: point to the service

---

### **B. Neo4j Service (Private Fargate)**

- In the same ECS Cluster:

  - Create Fargate Service:

    - Task Definition:

      - Container Image: `neo4j:5.19`
      - Environment Variable:

        - `NEO4J_AUTH=neo4j/password`

      - Port Mapping: 7687
      - Task Role: Attach `EcsTaskRole`

    - Service:

      - Desired Count: 1

    - Networking:

      - Subnets: `PrivateECS`
      - Assign public IP: **No**
      - Security Group: `ECS-SG`

---

## ✅ **Post-Provisioning Checklist**

- Verify:

  - Secrets contain all sensitive configs.
  - RDS is accessible only from ECS services.
  - ALB points correctly to FastAPI containers.
  - Neo4j service remains isolated without public exposure.
  - S3 permissions work as intended from ECS.
