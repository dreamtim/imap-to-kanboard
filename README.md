# imap-to-webhook

A stateless service is designed to build a relay between an IMAP server and Kanoard application in a simple,
convenient way, without delving into the format of the mail format.

It periodically retrieves IMAP messages from selected IMAP folder, parse them to create a Kanboard card containing email content and attachements
The message can be moved to another IMAP folder or deleted completely. In case of connection errors, the message is moved to another folder.

Created Kanboard card, among others includes:

 * extracted Plain text (or HTML converted to markdown if no plaintext available)
 * attachments matching specific formats ("pdf, "docx", "doc") - images are ignored
 * indication if the message comes from INBOX or SPAM folder as a TAG on the cards

## Configuration

Configuration takes place via a.ini file.

 The following configuration variables are supported:

Name                      | Description
--------------------------| -----------
```app_mode```            | Application mode DEBUG or PRODUCTION
```delay```               | Length of the interval between the next downloading of the message in seconds. Default: ```300```
```api_key```             | The kanboard API key
```api_url```             |The URL pointing to your kanboard instance (```http://yourdomain.tld/jsonrpc.php```)
```project_id```          | The id of the project in which the card have to be created
```transport```           | The type of transport ```imap+ssl``` or ```imap```
```hostname```            | The IMAP hostname ie ```mail.google.com``` or ``mail.infomaniak.com`` ...
```username```            | The IMAP username for login
```password```            | The IMAP password for login
```port```                | The port for IMAP connexion ie ```993``` for ssl
```inbox```               | Folder to download messages
```error```               | Folder to move messages on error (````error````)
```success```             | Folder to store messages on success (```success```)
```on_success```          | Action to perform on process messages. Available ```move```, ```delete```
```compress_eml```         | not Implemented Specifies whether the sent ```.eml``` file should be compressed or not. Example: ```true```

## Development

In order to facilitate the development, the docker-compose.yml file is provided.

```
$ git clone git@github.com:dreamtim/imap-to-kanboard.git
$ cd imap-to-webhook
$ cp .env.sample .env
$ docker-compose up
```

The following services are provided:

* ```daemon``` - proper service
* ```kanboard``` To be implemented.

## Testing

Following commands are required to run tests:

```
pip install -r requirements.txt
python test.py
```
