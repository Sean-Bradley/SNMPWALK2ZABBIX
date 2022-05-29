# Copyright Sean Bradley 2022
# Repository https://github.com/Sean-Bradley/SNMPWALK2ZABBIX
#
# LICENSE https://github.com/Sean-Bradley/SNMPWALK2ZABBIX/blob/main/LICENSE
#
# SNMPWALK2ZABBIX : Create a Zabbix template from an SNMPWALK response.
# Copyright (C) 2022 Sean Bradley
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys
import os
import re
import uuid

if len(sys.argv) < 3:
    print(
        "Usage: python snmpwalk2zabbix.py \x1B[3mCommunity\x1B[23m \x1B[3mIP-Address\x1B[23m \x1B[3mBase-OID\x1B[23m\neg,\npython snmpwalk2zabbix.py public 127.0.0.1 1.3.6.1.2.1.1")
else:
    COMMUNITY = sys.argv[1]
    IP = sys.argv[2]
    BASE_OID = sys.argv[3] if len(sys.argv) == 4 else "."

    OIDSRESPONSE = os.popen('snmpwalk -v 2c -On -c ' +
                            COMMUNITY + ' ' + IP + ' ' + BASE_OID).read()
    # MIBSRESPONSE = os.popen('snmpwalk -v 2c -OX -c ' +
    #                        COMMUNITY + ' ' + IP + ' ' + BASE_OID).read()

    OIDS = OIDSRESPONSE.split("\n")

    print("Processing " + str(len(OIDS)) + " rows")

    DATATYPES = {
        "STRING": "CHAR",
        "OID": "CHAR",
        "TIMETICKS": "",
        "BITS": "TEXT",
        "COUNTER": "",
        "COUNTER32": "",
        "COUNTER64": "",
        "GAUGE": "",
        "GAUGE32": "",
        "INTEGER": "FLOAT",
        "INTEGER32": "FLOAT",
        "IPADDR": "TEXT",
        "IPADDRESS": "TEXT",
        "NETADDDR": "TEXT",
        "NOTIF": "",  # SNMP Trap
        "TRAP": "",  # SNMP Trap
        "OBJECTID": "TEXT",
        "OCTETSTR": "TEXT",
        "OPAQUE": "TEXT",
        "TICKS": "",
        "UNSIGNED32": "",
        "WRONG TYPE (SHOULD BE GAUGE32 OR UNSIGNED32)": "TEXT",
        "\"\"": "TEXT",
        "HEX-STRING": "TEXT",
    }

    def getDataType(s):
        dataType = "TEXT"
        if s in DATATYPES:
            dataType = DATATYPES[s]

            if s == "NOTIF" or s == "TRAP":
                print("TODO: handle traps")
        else:
            print("Unhandled data type [" + s + "] so assigning TEXT")
        if len(dataType) > 0:  # if data type is INTEGER or other unsigned int, then don't create the node since zabbix will assign it the default which is already unsigned int
            return dataType
        else:
            return None

    ITEMS = []
    # ENUMS = {}
    # LAST_ENUM_NAME = ""  # the one that is being built now
    DISCOVERY_RULES = {}
    LAST_PART_10 = ""  # so that no duplcate table rows are re added
    TEMPLATE_NAME = "my template"

    for i, oid in enumerate(OIDS):
        if len(oid) > 0:  # and i < 7:
            #print(str(i) + " " + str(len(OIDS)) + " " + str(len(oid)))
            if not "NO MORE VARIABLES LEFT" in oid.upper():
                oid_kvp = oid.split("=")
                mib = oid_kvp  # set it to the OID in case MIB version can't be found
                if len(oid_kvp) > 1:  # and i != len(OIDS) - 1:
                    data_type = getDataType(
                        oid_kvp[1].split(":")[0].strip().upper())

                    if len(oid_kvp[1]) > 3:
                        value = oid_kvp[1].split(":")[1].strip()

                        if oid_kvp[0].strip() == ".1.3.6.1.2.1.1.5.0":
                            TEMPLATE_NAME = value

                        fullOidString = os.popen(
                            'snmptranslate -Of ' + oid_kvp[0].strip()).read()
                        if fullOidString is not None:
                            fullOidStringParts = fullOidString.split(".")

                        # restricts to only add tables and simple items
                        if len(fullOidStringParts) < 13:

                            mibString = os.popen(
                                'snmptranslate -Tz ' + oid_kvp[0].strip()).read()
                            if mibString is not None:
                                mib = mibString.strip()

                            description = os.popen(
                                'snmptranslate -Td ' + oid_kvp[0].strip()).read()
                            if description is not None:
                                groups = re.search(
                                    r'DESCRIPTION.*("[^"]*")', description)
                                if groups is not None:
                                    if groups.group(1) is not None:
                                        description = groups.group(1)
                                        description = description.replace(
                                            '"', '')
                                        description = description.replace(
                                            '\\n', '&#13;')
                                        description = description.replace(
                                            '<', '&lt;')
                                        description = description.replace(
                                            '>', '&gt;')
                                        description = re.sub(
                                            r"\s\s+", " ", description)
                                        # print(description)

                            #print(oid_kvp[0].strip() + ", " + mib + ", " + value)

                            if fullOidStringParts[8].upper().endswith("TABLE"):
                                # table = os.popen('snmptable -v 2c -c ' +
                                #     COMMUNITY + ' ' + IP + ' ' + fullOidStringParts[8]).read()
                                # print(table)
                                # exit()

                                name = mib.split("::")[0] + \
                                    "::" + fullOidStringParts[8]
                                #name = fullOidStringParts[8]
                                key = mib.replace("::", ".")
                                #print(fullOidStringParts[8] + " " + fullOidStringParts[9] + " " + fullOidStringParts[10])
                                if not name in DISCOVERY_RULES:
                                    DISCOVERY_RULES[name] = []
                                    LAST_PART_10 = ""

                                if LAST_PART_10 != fullOidStringParts[10]:
                                    trimmed_oid = oid_kvp[0].strip()
                                    trimmed_oid = trimmed_oid.split(".")[:-1]
                                    trimmed_oid = ".".join(trimmed_oid)
                                    # print(oid_kvp[0].strip())
                                    # print(trimmed_oid)
                                    # exit()
                                    item_protoype = [
                                        fullOidStringParts[10], mib, key, trimmed_oid, data_type, description]
                                    LAST_PART_10 = fullOidStringParts[10]
                                    # print(name)
                                    # print(discovery_rule)
                                    # exit()
                                    DISCOVERY_RULES[name].append(item_protoype)
                                    print("ITEM_PROTOTYPE -> " + name + " -> " + fullOidStringParts[10] + " (" + (
                                        "NUMERIC" if data_type is None else data_type) + ")")
                            else:
                                name = mib.split("::")[1]
                                name = name.split(".")[0]
                                key = mib.replace("::", ".")
                                item = [name, mib, key, oid_kvp[0].strip(),
                                        data_type, description]
                                ITEMS.append(item)
                                print("ITEM -> " + mib + " -> " + name + " (" +
                                      ("NUMERIC" if data_type is None else data_type) + ")")

    xml = """<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<zabbix_export>
    <version>6.0</version>
    <templates>
        <template>
            <uuid>""" + uuid.uuid4().hex + """</uuid>
            <template>""" + TEMPLATE_NAME + """ SNMP</template>
            <name>""" + TEMPLATE_NAME + """ SNMP</name>
            <description>Template built by SNMPWALK2ZABBIX script from https://github.com/Sean-Bradley/SNMPWALK2ZABBIX</description>
            <groups>
                <group>
                    <name>Templates</name>
                </group>
            </groups>
            <items>"""

    # ITEMS
    for item in ITEMS:
        # print(item)
        xml += """                  
                <item>
                    <uuid>""" + uuid.uuid4().hex + """</uuid>
                    <name>""" + item[0] + """</name>
                    <type>SNMP_AGENT</type>
                    <snmp_oid>""" + item[3] + """</snmp_oid>
                    <key>""" + item[2] + """</key>"""
        if item[4] is not None:
            xml += """                    
                    <value_type>""" + item[4] + """</value_type>"""
        xml += """
                    <description>""" + item[5] + """</description>
                    <history>7d</history>
                    <trends>0</trends>
                    <status>DISABLED</status>
                </item>"""
    if len(ITEMS):
        xml += """
            </items>"""

    # Discovery rules and item prototypes
    if len(DISCOVERY_RULES):
        xml += """
            <discovery_rules>"""
        for discovery_rule in DISCOVERY_RULES:
            # print(DISCOVERY_RULES[discovery_rule])
            SNMPOIDS = ""
            xml += """
                <discovery_rule>
                    <uuid>""" + uuid.uuid4().hex + """</uuid>
                    <name>""" + discovery_rule.split("::")[1] + """</name>
                    <delay>3600</delay>
                    <key>""" + discovery_rule.replace("::", ".") + """</key>
                    <status>DISABLED</status>
                    <type>SNMP_AGENT</type>
                    <item_prototypes>"""

            for item_protoype in DISCOVERY_RULES[discovery_rule]:
                # print(item_protoype)
                xml += """
                        <item_prototype>
                            <uuid>""" + uuid.uuid4().hex + """</uuid>
                            <name>""" + item_protoype[0] + """.{#SNMPINDEX}</name>
                            <type>SNMP_AGENT</type>
                            <snmp_oid>""" + item_protoype[3] + """.{#SNMPINDEX}</snmp_oid>
                            <key>""" + item_protoype[3] + """.[{#SNMPINDEX}]</key>"""
                if item_protoype[4] is not None:
                    xml += """                    
                            <value_type>""" + item_protoype[4] + """</value_type>"""
                xml += """
                            <delay>1h</delay>
                            <history>7d</history>
                            <description>""" + item_protoype[5] + """</description>                           
                        </item_prototype>"""

                SNMPOID2APPEND = "{#" + \
                    item_protoype[0].upper() + "}," + item_protoype[3] + ","
                if(len(SNMPOIDS + SNMPOID2APPEND) < 501):
                    SNMPOIDS += SNMPOID2APPEND

            xml += """                        
                    </item_prototypes>
                    <snmp_oid>discovery[""" + SNMPOIDS[:-1] + """]</snmp_oid>"""
            xml += """
                </discovery_rule>"""

        xml += """
            </discovery_rules>"""

    # #ENUMS
    # if len(ENUMS):
    #     xml += """
    #         <value_maps>"""
    #     for x in ENUMS:
    #         xml += """
    #             <value_map>
    #                 <name>""" + x + """</name>
    #                 <mappings>"""
    #         for y in ENUMS[x]:
    #             xml += """
    #                     <mapping>
    #                         <newvalue>""" + y[0] + """</newvalue>
    #                         <value>""" + y[1] + """</value>
    #                     </mapping>"""
    #         xml += """
    #                 </mappings>
    #             </value_map>"""
    #     xml += """
    #         </value_maps>"""

    xml += """
        </template>
    </templates>
</zabbix_export>"""

    with open("template-" + TEMPLATE_NAME.replace(" ", "-") + ".xml", "w") as xml_file:
        xml_file.write(xml)

    print("Done")
