/**
 * 
 */
package com.programming.array;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * @author govind.gupta
 *
 */
public class DialPad {
	
	public final String[] dialPadKeys = {"abc", "def", "ghi", "jkl", "mno", "pqrs", "tuv", "wxyz"};

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		// TODO Auto-generated method stub
		fillDialPadMap();
		List<String> comb = letterCombinations("342");
		for (String let : comb)
		{
			System.out.println(let);
		}
		permComb("237");
	}
	
	static Map<Integer, String> dialPadMap = new HashMap<Integer, String>(); 
	
	static final void fillDialPadMap()
	{
		dialPadMap.put(2, "abc");
		dialPadMap.put(3, "def");
		dialPadMap.put(4, "ghi");
		dialPadMap.put(5, "jkl");
		dialPadMap.put(6, "mno");
		dialPadMap.put(7, "pqrs");
		dialPadMap.put(8, "tuv");
		dialPadMap.put(9, "wxyz");
	}

	public static void permComb(String dialNum)
	{
		List<String> perm = new ArrayList<String>();
		List<String> temp = new ArrayList<String>();
		perm.add("");
		for (int i=0;i<dialNum.length();i++)
		{
			for (String str : perm)
			{
				String letters = dialPadMap.get(dialNum.charAt(i) - '0');
				for (int j =0; j<letters.length(); j++)
				{
					temp.add(str+letters.charAt(j));
				}
			}
			perm = temp;
			temp = new ArrayList<String>();
		}
		for (String str : perm)
		{
			System.out.println(str);
		}
	}
	
	
    public static ArrayList<String> letterCombinations(String digits) {
        ArrayList<String> res = new ArrayList<String>();
        ArrayList<String> preres = new ArrayList<String>();
        res.add("");

        for(int i=0;i<digits.length();i++){
            for(String str: res)
            {
                String letters = dialPadMap.get((int)(digits.charAt(i)-'0'));
                for(int j=0;j<letters.length();j++)
                {
                    preres.add(str+letters.charAt(j));
                }
            }
            res = preres;
            preres = new ArrayList<String>();
        }      
        return res;
    }
}
