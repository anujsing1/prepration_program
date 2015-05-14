/**
 * 
 */
package com.crest;

import java.util.ArrayList;
import java.util.Scanner;

/**
 * @author govind.gupta
 *
 */
public class DrawShape {
	
	public static Shape shape;
	public static ArrayList<Shape> shapes;
	public static int cWidth;
	public static int cHeight;
	public static boolean quit = false;
	static StringBuilder canvas = null;

	/**
	 * @param args
	 */
	public static void main(String[] args) {
		int x1=0, y1=0, x2=0, y2=0;
		Character cmd = null;
		shapes = new ArrayList<Shape>();

        do
        {
        	System.out.println("Please enter a command: ");
   	     
            Scanner inputCmd = new Scanner(System.in);
           
            String command = inputCmd.nextLine();
            String[] inputs = command.split(" ");
            System.out.println("Command Entered " + command);
            if (inputs.length >= 1)
            {
            	cmd = inputs[0].charAt(0);
            }
        	if (inputs.length >= 3)
        	{
	        	x1 = Integer.parseInt(inputs[1]);
	        	y1 = Integer.parseInt(inputs[2]);
        	}
        	if (inputs.length == 5)
        	{
	        	x2 = Integer.parseInt(inputs[3]);
	        	y2 = Integer.parseInt(inputs[4]);
        	}
        	drawShape(cmd, x1, y1, x2, y2);
        }while(!quit);
	}
	
	/**
	 * @param cmd
	 * @param x1
	 * @param y1
	 * @param x2
	 * @param y2
	 */
	private static void drawShape(Character cmd, int x1, int y1, int x2, int y2) {
		if ('Q' == Character.toUpperCase(cmd))
		{
			quit = true;
			System.out.println("System Exit!");
		}
		else
		{
			if('C' == Character.toUpperCase(cmd))
			{
				cWidth = x1;
				cHeight = y1;
				createCanvasString();
				System.out.println();
			}
			else if ('L' == Character.toUpperCase(cmd) || 'R' == Character.toUpperCase(cmd))
			{
				shape = new Shape(Character.toUpperCase(cmd), x1, y1, x2, y2);
				shapes.add(shape);
				createCanvasString();
				System.out.println();
			}
		}
	}

	/**
	 * 
	 */
	public static void createCanvasString()
	{
		canvas = new StringBuilder();
		StringBuilder hLine = createHorizontalLine(cWidth, '-');
		canvas.append(hLine);
		canvas.append("\n");
		
		for(int i=0;i<cHeight;i++)
		{
			canvas.append("|");
			for(int j=0;j<cWidth-2;j++)
			{
				for (Shape s : shapes)
				{
					int x1 = s.getX1(), y1 = s.getY1(), x2 = s.getX2(), y2 = s.getY2();
					if (s.getCmd() == 'L')
					{
						drawLine(i, j, x1, y1, x2, y2);
					}
					else if (s.getCmd() == 'R')
					{
						drawRectangle(i, j, x1, y1, x2, y2);
					}
				}
				canvas.append(" ");
			}
			canvas.append("|");
			canvas.append("\n");
		}
		canvas.append(hLine);
		System.out.println(canvas);
	}
	
	/**
	 * @param i
	 * @param j
	 * @param x1
	 * @param y1
	 * @param x2
	 * @param y2
	 */
	public static void drawRectangle(int i, int j, int x1, int y1, int x2, int y2)
	{
		StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
		if (i+1 == y1 || i+1 == y2)
		{
			if (j+1 == x1)
				System.out.print(lineToDraw);
		}
		else if (i+1 < y2 && i+1 > y1)
		{
			if(j+1 == x2-2 || j+1 == x1)
			{
				System.out.print('x');
			}
		}
	}
	
	/**
	 * @param i
	 * @param j
	 * @param x1
	 * @param y1
	 * @param x2
	 * @param y2
	 */
	public static void drawLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		if (y1 == y2)
		{
			drawHLine(i, j, x1, y1, x2, y2);
		}
		else if (x1==x2)
		{
			drawVLine(i, j, x1, y1, x2, y2);
		}
	}
	
	/**
	 * @param i
	 * @param j
	 * @param x1
	 * @param y1
	 * @param x2
	 * @param y2
	 */
	public static void drawVLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		if (i+1 >= y1 && i+1 <= y2)
		{
			if (x1 == j+1)
				canvas.append("x");
		}
	}
	
	/**
	 * @param i
	 * @param j
	 * @param x1
	 * @param y1
	 * @param x2
	 * @param y2
	 */
	public static void drawHLine(int i, int j, int x1, int y1, int x2, int y2)
	{
		StringBuilder lineToDraw = createHorizontalLine(x2-x1, 'x');
		if (i+1 == y1)
		{
			if (x1 == j+1)
			{
				canvas.append(lineToDraw);
			}
		}
	}
	
	/**
	 * @param width
	 * @param c
	 * @return
	 */
	public static StringBuilder createHorizontalLine(int width, char c)
	{
		StringBuilder verticalLine = new StringBuilder();
		for (int i=0;i<width;i++)
		{
			verticalLine = verticalLine.append(c);
		}
		return verticalLine;
	}
}
