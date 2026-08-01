/* FieldRules.java  v001  221108  jrt  */
/*
 Name:        FieldRules.java
 Intention:   ISO 8583 field 48 subelement layout rules
*/
package tools.validation;

public class FieldRules {
    public static boolean checkSubelementLayout(String field48) {
        return field48 != null && field48.length() >= 4;
    }
}
