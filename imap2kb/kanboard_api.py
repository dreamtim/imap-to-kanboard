import kanboard
import base64
import os
import eml_parser
import html2text

import logging


class KanboardApi :

    def __init__(self,project_id,api_url,api_key, allowed_attachments_type = [".docx",".pdf",".doc"]):

        self.kb = kanboard.Client(api_url, 'jsonrpc', api_key)
        self.allowed_attachments_type = allowed_attachments_type
        self.project_id = project_id

    def attach_file_to_task(self,task_id,filepath,filename):
        data = open(os.path.join(filepath,filename), "rb").read()
        encoded = base64.b64encode(data).decode("utf-8")
        file_id = self.kb.create_task_file(project_id=self.project_id,task_id=self.task_id,filename=filename,blob=encoded)

    def attach_eml_to_task(self,task_id,filepath,emlfilename):
        self.attach_file_to_task(task_id,filepath,emlfilename)

    def create_task(self,title,description,tags=[],colorid="grey") :
        task_id = self.kb.create_task(project_id=self.project_id, title=title,description=description,tags=tags,color_id=colorid)
        #kb.create_task(project_id=project_id, title='My task title',description="My description")
        return task_id

    def create_task_from_eml(self,mail,isspam=False) :
        """

        Parameters
        ----------
        kb : A bankord api object
            DESCRIPTION.
        project_id : The id of the banboard project
            DESCRIPTION.
        mail : Raw email content
            DESCRIPTION.

        Returns
        -------
        task_id : The task id created or null if error
            DESCRIPTION.

        """
        mail,valid_attachments,mail_content = parse_mail_content(mail)
        task_title = mail.subject
        task_description = mail_content

        print("Processing Email {:.50s} ...".format(mail.subject))

        tags = ""
        if isspam :
            tags = ["SPAM"]
            color="grey"
        else :
            tags = ["INBOX"]
            color= "grey"

        task_id = self.create_task(task_title,task_description,colorid=color,tags=tags)


        # task_id = create_task(kb,project_id,task_title,task_description)

        print("Created new task with id {}".format(task_id))

        for attachment in valid_attachments :
            attfilename = attachment.get("filename",None)
            attcontent = attachment.get("payload",None)

            if ((attfilename is not None) and (attcontent is not None)):
                file_id = self.kb.create_task_file(project_id=self.project_id,task_id=task_id,filename=attfilename,blob=attcontent)
                print("Attached file with ID {}".format(file_id))

        return task_id


def filter_allowed_attachments (attachments_in_list,allowed_attachments_type=[".docx",".pdf",".doc"]) :
    """
    A function to filter a list of attachements dictionnary and keep only the files with extensions matching allowed_attachments_type list

    Parameters
    ----------
    attachments_in_list : a list of attachements dictionnary (binar, charset, \
                                                              content-id, content_transfer_encoding, filename
    ,mail_content_type, payload)

    allowed_attachments_type : an array of allowed file extension [".docx",".pdf",".doc"]

    Return
    ----------
    a list of attachments dictionnary

    """
    attachments_out_list = []

    if len(attachments_in_list)==0:
        return attachments_out_list


    for attachment in attachments_in_list :
        filename = attachment.get("filename","")

        logger = logging.getLogger('root')

        logger.info("filename")

        print(filename)

        name, extension = os.path.splitext(filename)
        if extension in allowed_attachments_type :
            print ("{:s} matched relevant attachment of type {:s}".format(filename,extension))
            attachments_out_list.append(attachment)


    return attachments_out_list


def sanitize_email_content(mail) :
    """A function that concatenate email parts into a single text string. It will prefer plain text content or try to convert html into markdown"""

    m = ""

    ## Prefer plain text content
    if len(mail.text_plain)>0 :

        for plain_part in mail.text_plain :
            m = m + "  " + plain_part

        return m

    ## Otherwise try to convert it to markdown
    else :
        m = ""

        parser = html2text.HTML2Text()
        parser.ignore_images = True
        parser.ignore_tables = True

        for html_part in mail.text_html :
            m = m + "  "+parser.handle(html_part)

            # +markdownify.markdownify(html_part, heading_style="ATX",strip=["meta","style","head"])
        return m



def read_mail(filepath,mailfile):
    mail = eml_parser.open_eml(filepath,mailfile)
    return mail


def parse_mail_content(mail):
    # print(mail.subject)
    # print(mail.to)
    # print(mail.text_plain)
    # print(mail.text_html)
    valid_attachments = filter_allowed_attachments(mail.attachments)
    mail_content = sanitize_email_content(mail)
    # setattr(mail,"attachments",valid_attachments)
    # mail.set_attachments(valid_attachments)
    return mail, valid_attachments, mail_content