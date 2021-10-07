# Github→Discord webhook example

This Yandex.Cloud Function accepts an _Issue_ event from Github and posts a message on Discord using a Discord webhook.

## Create the Discord webhook

1. [How to create a webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)
2. Copy the webhook URL

## Creating the function

1. Make a new Yandex.Cloud Function
2. Copy all the files from this folder into the code editor
3. Create an environment variable `DISCORD_WEBHOOK` with the webhook URL:

![image](https://user-images.githubusercontent.com/42166884/136457685-96d88bc0-9b6c-4f88-b04e-0f62d301ae55.png)

## Make GitHub call our function

1. Copy the URL of the function:

![image](https://user-images.githubusercontent.com/42166884/136458340-5f8ef0ac-94ad-46e5-9180-56c6aa4035e8.png)

2. Open your GitHub repository
3. Go to **Settings**
4. Go to **Webhooks**
5. Click on **Add webhook**
6. Paste the function URL into the **Payload URL** field
7. Select **Let me select individual events** under **Which events would you like to trigger this webhook?**, check **Issues** and uncheck **Pushes**
8. Change **Content type** to **`application/json`**
9. Click on **Add webhook**

Now open an issue and then close it. You should see two embeds like this in the channel where you created the Discord webhook:

![image](https://user-images.githubusercontent.com/42166884/136458749-7eb753b7-a036-4f8b-9380-b200879b4a32.png)

