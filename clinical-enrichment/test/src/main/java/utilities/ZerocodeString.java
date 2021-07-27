/*******************************************************************************
 * IBM Confidential OCO Source Materials
 * 5737-D31, 5737-A56
 * (C) Copyright IBM Corp. 2020, 2021
 *
 * The source code for this program is not published or otherwise
 * divested of its trade secrets, irrespective of what has
 * been deposited with the U.S. Copyright Office.
 *******************************************************************************/
package utilities;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Objects;

public class ZerocodeString {
    private String string1;
    private String string2;
    private String result;

    @JsonCreator
    public ZerocodeString(
    		@JsonProperty("result")String result,
            @JsonProperty("string1")String string1,
            @JsonProperty("string2")String string2) {
    	this.string1 = string1;
        this.string2 = string2;
        this.result = "";
    }

    public String getString1() {
        return string1;
    }

    public String getString2() {
        return string2;
    }

    public String getResult() {
        return result;
    }
    
    public void setString1(String str) {
    	this.string1 = str;
    }
    
    public void setString2(String str) {
    	this.string2 = str;
    }
    
    public void setResult(String newResult) {
        this.result = newResult;
    }

}
