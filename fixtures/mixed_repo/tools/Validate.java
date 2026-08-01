/* Validate.java  v002  230114  jrt  */
/*
 Name:        Validate.java
 PURPOSE:     entry point for acquirer message validation
*/
package tools;

import tools.validation.FieldRules;
import tools.validation.BrandRules;

public class Validate {
    public static boolean validateMessage(String mti, String field48) {
        if (!FieldRules.checkSubelementLayout(field48)) {
            return false;
        }
        return BrandRules.checkBrandConstraints(mti);
    }
}
