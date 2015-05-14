/**
 * 
 */
package com.study;


/**
 * @author govind.gupta
 *
 */
abstract class PersistentTest_Q13 {

	public static void main(String[] args) {
//		System.out.println("sa"+(new String('v'+'a')));
		Object obj1 = new Object();
		Object obj2 = obj1;
		if(obj1.equals(obj2))System.out.println(true);
		else System.out.println(false);
		if(obj1 == obj2)System.out.println(true);
		else System.out.println(false);
	}
}
