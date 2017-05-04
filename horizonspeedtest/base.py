#    Copyright 2015 Reliance Jio Infocomm, Ltd.
#    Author: Alok Jani <Alok.Jani@ril.com>
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# -----------------------------------------------------------

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

from horizonspeedtest import exceptions

class HorizonSpeedTest(object):
    def __init__(self, username, password, auth_type, 
            horizon_login_url, horizon_switch_tenant_url, horizon_volumes_url, 
	    horizon_instances_url, horizon_networks_url, horizon_images_url,
	    horizon_logout_url,show_browser=False):
        """ Initialize parameters for the target cloud """
        self.username = username
        self.password = password
        self.auth_type = auth_type
        self.horizon_login_url = horizon_login_url
        self.horizon_switch_tenant_url = horizon_switch_tenant_url
        self.horizon_volumes_url = horizon_volumes_url
        self.horizon_networks_url = horizon_networks_url
        self.horizon_instances_url = horizon_instances_url
        self.horizon_images_url = horizon_images_url
        self.horizon_logout_url = horizon_logout_url
        self.show_browser = show_browser
        self.driver = None
        self.display = None

	self.error_file = open("errors.txt", "w")
	self.error_file.close()

        if self.show_browser is False:
           self.display = Display(visible=0, size=(800, 600))
           self.display.start()

	fp = webdriver.FirefoxProfile()
	# Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
	#fp.set_preference("network.proxy.type", 0)
	#self.driver = webdriver.Firefox(firefox_profile=fp)

        self.driver = webdriver.Firefox()


    def login_into_horizon(self):
        """ first login into Horizon Dashboard """
        logging.info("logging into {}".format(self.horizon_login_url))
        try:
            self.driver.get(self.horizon_login_url)
            pageElement = Select(self.driver.find_element_by_name("auth_type"))
            if self.auth_type == 'Keystone':
                pageElement.select_by_value('credentials')
                #pageElement.select_by_visible_text('Keystone Credentials')
                pageElement = self.driver.find_element_by_name("username")
                pageElement.send_keys(self.username)
                pageElement = self.driver.find_element_by_name("password")
                pageElement.send_keys(self.password)
	        pageElement = self.driver.find_element_by_css_selector("button[type='submit']")
	        pageElement.click()
            else:
                #pageElement.select_by_value('saml2')
	        pageElement = self.driver.find_element_by_id("loginBtn")
	        pageElement.click()
                element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username")))
	        #pageElement = self.driver.find_element_by_name("Connect")
                pageElement = self.driver.find_element_by_name("username")
                pageElement.send_keys(self.username)
                pageElement = self.driver.find_element_by_name("password")
                pageElement.send_keys(self.password)
	        pageElement = self.driver.find_element_by_css_selector("input[type='submit'][value='Login']")
	        pageElement.click()

        except NoSuchElementException:
            raise exceptions.PageSourceException("Element not found")

        navigationStart = self.driver.execute_script(
                "return window.performance.timing.navigationStart")
        responseStart   = self.driver.execute_script(
                "return window.performance.timing.responseStart")
        domComplete     = self.driver.execute_script(
                "return window.performance.timing.domComplete")

        if "Invalid" in self.driver.page_source:
            raise exceptions.LoginFailureException('Invalid Username/Password')

        backendPerformance = responseStart - navigationStart
        frontendPerformance = domComplete - responseStart
        totalTime = (backendPerformance + frontendPerformance) 

        logging.info("load time [Login Page] is {} ms".format(totalTime))

        return { 'Login Page': str(totalTime) + " ms" }


    def switch_horizon_tenant(self):
        """ Switch to the tenant underwhich we want test browser calls """
        logging.info("switching tenant {}".format(self.horizon_switch_tenant_url))
        self.driver.get(self.horizon_switch_tenant_url)


    def logout_from_horizon(self):
        """ Ensure that we logout from the browser before we exit """
        self.driver.get(self.horizon_logout_url)
        logging.info("logging out of horizon {}".format(self.horizon_logout_url))
        self._driverQuit()


    def _load_page_measure_time(self, driver, source, tag):
        """ program core that GETs the URL, computes browser load time """
        self.driver.get(source)
        navigationStart = driver.execute_script(
                "return window.performance.timing.navigationStart")
        responseStart   = driver.execute_script(
                "return window.performance.timing.responseStart")
        domComplete     = driver.execute_script(
                "return window.performance.timing.domComplete")

        backendPerformance = responseStart - navigationStart
        frontendPerformance = domComplete - responseStart
        totalTime = (backendPerformance + frontendPerformance) 

        logging.info("load time [%s] is %s ms" % (tag,totalTime))

        if "Error: " in self.driver.page_source:
	    try:
                error_msg = self.driver.find_element_by_css_selector("html > body > div#container > div#main_content > div.messages > div.alert.alert-danger.alert-dismissable.fade.in > p")
            except Exception as inst:
                with open("errors.txt", "a") as myfile:
		    myfile.write(type(inst))
                    myfile.write(source)
                    myfile.write(tag)
                    myfile.write(error_msg.text)

        return { tag: str(totalTime) + " ms" }


    def load_images_page(self):
        """ Navigate to Images Page """
        logging.info("loading images page {}".format(self.horizon_images_url))

        return self._load_page_measure_time(self.driver,self.horizon_images_url,
                tag = "Images Page")


    def load_instances_page(self):
        """ Navigate to Instances Page """
        logging.info("loading instances page {}".format(self.horizon_instances_url))

        return self._load_page_measure_time(self.driver, self.horizon_instances_url,
                tag = "Instances Page")


    def load_networks_page(self):
        """ Navigate to the Networks Page """
        logging.info("loading networks page {}".format(self.horizon_networks_url))

        return self._load_page_measure_time(self.driver, self.horizon_networks_url,
                tag = "Networks Page")

    def load_volumes_page(self):
        """ Navigate to the Volumes Page """
        logging.info("loading volumes page {}".format(self.horizon_volumes_url))

        return self._load_page_measure_time(self.driver, self.horizon_volumes_url,
                tag = "Volumes Page")


    def _driverQuit(self):
        self.driver.close()
	if self.show_browser is False:
           self.display.stop()
