# Lab 01: Deploy and Autoscale an Azure Virtual Machine Scale Set

### Estimated Duration: 60 Minutes

## Lab Overview

In this lab, you will create an Azure Virtual Machine Scale Set (VMSS) in Flexible orchestration mode, backed by a Standard Load Balancer. You will configure the VMSS with a Windows Server image, attach it to a pre-provisioned virtual network, and set up custom autoscale rules based on CPU utilization. Finally, you will verify instance distribution across availability zones and review the scale set overview.

## Lab Objectives

In this lab, you will complete the following tasks:

- Task 1: Create a Standard Load Balancer for the Scale Set  
- Task 2: Deploy the Virtual Machine Scale Set with Flexible Orchestration  
- Task 3: Configure Custom Autoscale Rules (Scale-Out and Scale-In)  
- Task 4: Verify Instance Distribution and Review the Scale Set Overview  

## Task 1: Create a Standard Load Balancer for the Scale Set

In this task, you will provision a Standard Load Balancer in the Azure portal to distribute traffic across VM instances in your scale set.

1. Navigate to the Azure portal and use the search bar to find **Load Balancers**.  
   ![](../media/search-loadbalancer.png)

2. On the **Load Balancers** blade, click **+ Create**.  
   ![](../media/click-create-loadbalancer.png)

3. On the **Basics** tab, configure the following settings:  
   - **Subscription**: Your subscription  
   - **Resource group**: Select the lab resource group  
   - **Name**: `lb-<inject key="DeploymentID" enableCopy="false"></inject>`  
   - **Region**: `<inject key="Region" enableCopy="false"></inject>`  
   - **SKU**: **Standard**  
   ![](../media/loadbalancer-basics.png)

4. Switch to the **Frontend IP** tab, click **+ Add**, and configure:  
   - **Name**: `pip-lb-<inject key="DeploymentID" enableCopy="false"></inject>`  
   - **IP version**: **IPv4**  
   - **SKU**: **Standard**  
   - **Assignment**: **Static**  
   ![](../media/loadbalancer-frontend.png)

5. Switch to the **Backend pools** tab, click **+ Add**, and set:  
   - **Name**: `be-lb-<inject key="DeploymentID" enableCopy="false"></inject>`  
   ![](../media/loadbalancer-backend.png)

6. Click **Review + create**, verify validation passes, then click **Create**.  
   ![](../media/loadbalancer-review.png)

> **Note:** Load Balancer must be created BEFORE the VMSS so it can be selected during VMSS creation.

<validation step="placeholder-guid-task1" />

> **Congratulations** on completing the task! You have successfully created a Standard Load Balancer for your scale set.

## Task 2: Deploy the Virtual Machine Scale Set with Flexible Orchestration

In this task, you will deploy a Virtual Machine Scale Set in Flexible orchestration mode, attach it to the pre-provisioned virtual network, and associate it with the Standard Load Balancer you created.

1. In the Azure portal, search for **Virtual Machine Scale Sets** and click **+ Create**.  
   ![](../media/search-vmss.png)

2. On the **Basics** tab under **Project details**, ensure the correct **Subscription** and **Resource group** are selected. Under **Scale set details**, configure:  
   - **Name**: `vmss-<inject key="DeploymentID" enableCopy="false"></inject>`  
   - **Region**: `<inject key="Region" enableCopy="false"></inject>`  
   - **Orchestration mode**: **Flexible**  
   - **Security type**: **Trusted launch virtual machines**  
   ![](../media/vmss-basics.png)

3. Under **Scaling**, set:  
   - **Instance count**: `2`  
   ![](../media/vmss-scaling.png)

4. Under **Instance details**, select **Image**: **Windows Server 2022 Datacenter**. Configure an administrator account:  
   - **Username**: `azureuser`  
   - **Password**: `<inject key="AzureAdUserPassword"></inject>`  
   ![](../media/vmss-instance-details.png)

5. Click **Next: Networking**. On the **Networking** tab:  
   - **Virtual network**: Select the pre-provisioned VNet in the lab resource group  
   - **Subnet**: Select the default subnet  
   - **Load balancing**:  
     - **Load balancer**: Select `lb-<inject key="DeploymentID" enableCopy="false"></inject>`  
     - **Backend pool**: Select `be-lb-<inject key="DeploymentID" enableCopy="false"></inject>`  
   ![](../media/vmss-networking.png)

6. Click **Review + create**, confirm the settings, and click **Create**.  
   ![](../media/vmss-review.png)

> **Note:** Overprovision is disabled by default in Flexible mode.

<validation step="placeholder-guid-task2" />

> **Congratulations** on completing the task! Your VM scale set has been deployed with Flexible orchestration.

## Task 3: Configure Custom Autoscale Rules (Scale-Out and Scale-In)

In this task, you'll create custom autoscale rules to adjust the number of VM instances based on average CPU utilization.

1. In the Azure portal, navigate to the lab resource group and select the scale set `vmss-<inject key="DeploymentID" enableCopy="false"></inject>`.  
   ![](../media/navigate-vmss.png)

2. In the left-hand menu of the VMSS blade, click **Scaling**.  
   ![](../media/vmss-scaling-menu.png)

3. Select **Custom autoscale**, then configure **Instance limits**:  
   - **Minimum instances**: `2`  
   - **Maximum instances**: `10`  
   - **Default (initial) instances**: `2`  
   ![](../media/autoscale-limits.png)

4. Click **Add a rule** to configure the scale-out rule:  
   - **Metric source**: **Virtual Machine Scale Set**  
   - **Metric name**: **Percentage CPU**  
   - **Condition**: **Greater than**  
   - **Threshold**: `70`  
   - **Time aggregation**: **Average**  
   - **Time window**: **10 minutes**  
   - **Action**: **Increase count by percent**: `20`  
   - **Cooldown**: **5 minutes**  
   ![](../media/autoscale-scaleout.png)

5. Click **Add a rule** again to configure the scale-in rule:  
   - **Metric name**: **Percentage CPU**  
   - **Condition**: **Less than**  
   - **Threshold**: `30`  
   - **Time aggregation**: **Average**  
   - **Time window**: **10 minutes**  
   - **Action**: **Decrease count by percent**: `20`  
   - **Cooldown**: **5 minutes**  
   ![](../media/autoscale-scalein.png)

6. Click **Save** to apply the autoscale configuration.  
   ![](../media/autoscale-save.png)

> **Note:** Scale-in may cause running tasks to stop abruptly after the cooldown period.

<validation step="placeholder-guid-task3" />

> **Congratulations** on completing the task! Your custom autoscale rules are now configured.

## Task 4: Verify Instance Distribution and Review the Scale Set Overview

In this task, you will verify the distribution of VM instances across availability zones and review your scale set configuration.

1. In the Azure portal, go to **Virtual Machine Scale Sets**, then select `vmss-<inject key="DeploymentID" enableCopy="false"></inject>`.  
   ![](../media/vmss-overview.png)

2. In the left-hand menu, click **Instances** to view all VM instances. Observe the **Availability zone** column to confirm zone distribution.  
   ![](../media/vmss-instances.png)

3. Return to the **Overview** tab of the scale set to review the summary of your deployment and autoscale settings.  
   ![](../media/vmss-summary.png)

<validation step="placeholder-guid-task4" />

> **Congratulations** on completing the task! You have verified instance distribution and reviewed the scale set overview.

## Summary

In this lab, you provisioned a Standard Load Balancer, deployed a Virtual Machine Scale Set in Flexible orchestration mode, configured CPU-based autoscale rules, and verified VM distribution across availability zones. You now have a scale set that automatically scales out and in based on workload, ensuring efficient resource utilization.

### Congratulations on completing the lab!